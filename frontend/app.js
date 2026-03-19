const { createApp, ref, onMounted, computed, watch } = Vue;

// Helper for debounce implementation
window._ = {
    debounce: (func, wait) => {
        let timeout;
        return function (...args) {
            clearTimeout(timeout);
            timeout = setTimeout(() => func.apply(this, args), wait);
        };
    }
};

// --- Dashboard Component ---
const DashboardView = {
    template: `
        <div>
            <h2>Financial Overview</h2>
            <div class="grid">
                <!-- Spending Donut -->
                <div class="card">
                    <h3>Spending by Category</h3>
                    <div style="height: 250px; position: relative;">
                        <canvas id="spendingChart"></canvas>
                        <div v-if="loading" style="position: absolute; top:50%; left:50%; transform: translate(-50%, -50%);">
                            Loading...
                        </div>
                    </div>
                </div>
                
                <!-- Cashflow Chart -->
                <div class="card">
                    <h3>Cashflow (6 Months)</h3>
                    <div style="height: 250px; position: relative;">
                        <canvas id="cashflowChart"></canvas>
                        <div v-if="loading" style="position: absolute; top:50%; left:50%; transform: translate(-50%, -50%);">
                            Loading...
                        </div>
                    </div>
                </div>
            </div>
        </div>
    `,
    setup() {
        const loading = ref(true);
        let spendingChart = null;
        let cashflowChart = null;

        const fetchData = async () => {
            loading.value = true;
            try {
                const response = await axios.get('/api/analytics/dashboard');
                renderCharts(response.data);
            } catch (error) {
                console.error("Error loading dashboard data:", error);
            } finally {
                loading.value = false;
            }
        };

        const renderCharts = (data) => {
            // Destroy existing charts if any
            if (spendingChart) spendingChart.destroy();
            if (cashflowChart) cashflowChart.destroy();

            // Spending Donut
            const ctxDonut = document.getElementById('spendingChart').getContext('2d');
            spendingChart = new Chart(ctxDonut, {
                type: 'doughnut',
                data: {
                    labels: data.donut.labels,
                    datasets: [{
                        data: data.donut.values,
                        backgroundColor: data.donut.colors,
                        borderWidth: 0
                    }]
                },
                options: {
                    responsive: true,
                    maintainAspectRatio: false,
                    plugins: {
                        legend: { position: 'right' }
                    }
                }
            });

            // Cashflow Line
            const ctxLine = document.getElementById('cashflowChart').getContext('2d');
            cashflowChart = new Chart(ctxLine, {
                type: 'line',
                data: {
                    labels: data.cashflow.labels,
                    datasets: [
                        {
                            label: 'Income',
                            data: data.cashflow.income,
                            borderColor: '#10B981', // green-500
                            backgroundColor: 'rgba(16, 185, 129, 0.1)',
                            fill: true,
                            tension: 0.4
                        },
                        {
                            label: 'Expenses',
                            data: data.cashflow.expense,
                            borderColor: '#EF4444', // red-500
                            backgroundColor: 'rgba(239, 68, 68, 0.1)',
                            fill: true,
                            tension: 0.4
                        }
                    ]
                },
                options: {
                    responsive: true,
                    maintainAspectRatio: false,
                    scales: {
                        y: { beginAtZero: true }
                    }
                }
            });
        };

        onMounted(() => {
            fetchData();
        });

        return { loading };
    }
};

// --- Transactions Component ---
const TransactionsView = {
    template: `
        <div>
            <h2>Transactions</h2>
            
            <div style="margin-bottom: 20px;">
                <input v-model="searchQuery" @input="debouncedSearch" type="text" placeholder="Search transactions..." style="width: 300px;">
                <button @click="openAddModal">➕ Add New</button>
            </div>
            
            <table>
                <thead>
                    <tr>
                        <th>Date</th>
                        <th>Category</th>
                        <th>Description</th>
                        <th>Amount</th>
                        <th>Actions</th>
                    </tr>
                </thead>
                <tbody>
                    <tr v-for="t in transactions" :key="t.id">
                        <td>{{ t.date }}</td>
                        <td>
                            <span :style="{ backgroundColor: t.category_color + '40', color: t.category_color, padding: '2px 5px', border: '1px solid ' + t.category_color }">
                                {{ t.category_name }}
                            </span>
                        </td>
                        <td>{{ t.description }}</td>
                        <td :class="t.type === 'income' ? 'text-green' : 'text-red'">
                            {{ t.type === 'income' ? '+' : '-' }}€{{ t.amount.toFixed(2) }}
                        </td>
                        <td style="text-align: center;">
                            <button @click="openEditModal(t)" title="Edit" style="margin-right: 5px;">✏️</button>
                            <button @click="deleteTransaction(t.id)" title="Delete">🗑️</button>
                        </td>
                    </tr>
                    <tr v-if="transactions.length === 0">
                        <td colspan="5" style="text-align: center; padding: 20px;">
                            No transactions found.
                        </td>
                    </tr>
                </tbody>
            </table>
            
            <div style="display: flex; justify-content: space-between; align-items: center; margin-top: 10px;">
                <button @click="prevPage" :disabled="currentPage === 1">Previous</button>
                <span>Page {{ currentPage }} of {{ totalPages }}</span>
                <button @click="nextPage" :disabled="currentPage === totalPages">Next</button>
            </div>
            
            <!-- Add Modal -->
            <div v-if="showAddModal" class="modal-overlay">
                <div class="modal">
                    <div class="modal-header">
                        <h2>{{ isEditing ? 'Edit Transaction' : 'Add Transaction' }}</h2>
                        <button @click="showAddModal = false" class="close-btn">❌</button>
                    </div>
                    
                    <div class="modal-content">
                        <div class="form-group">
                            <label>Type</label>
                            <select v-model="newForm.type" style="width: 100%;">
                                <option value="expense">Expense</option>
                                <option value="income">Income</option>
                            </select>
                        </div>
                        
                        <div class="form-group">
                            <label>Date</label>
                            <input v-model="newForm.date" type="date" style="width: 100%;">
                        </div>
                        
                        <div class="form-group">
                            <label>Category</label>
                            <select v-model="newForm.category_id" style="width: 100%;">
                                <option v-for="c in categories" :key="c.id" :value="c.id">{{ c.name }}</option>
                            </select>
                        </div>
                        
                        <div class="form-group">
                            <label>Amount (€)</label>
                            <input v-model.number="newForm.amount" type="number" step="0.01" style="width: 100%;">
                        </div>
                        
                        <div class="form-group">
                            <label>Description</label>
                            <input v-model="newForm.description" type="text" style="width: 100%;">
                        </div>
                        
                        <div style="margin-top: 20px; text-align: right;">
                            <button @click="submitTransaction">💾 Save</button>
                        </div>
                    </div>
                </div>
            </div>
        </div>
    `,
    setup() {
        const transactions = ref([]);
        const searchQuery = ref('');
        const currentPage = ref(1);
        const totalPages = ref(1);
        const showAddModal = ref(false);
        const isEditing = ref(false);
        const editingId = ref(null);
        const categories = ref([]);

        const newForm = ref({
            type: 'expense',
            amount: '',
            date: new Date().toISOString().slice(0, 10),
            description: '',
            category_id: null
        });

        const openAddModal = () => {
            isEditing.value = false;
            editingId.value = null;
            newForm.value = {
                type: 'expense',
                amount: '',
                date: new Date().toISOString().slice(0, 10),
                description: '',
                category_id: categories.value.length > 0 ? categories.value[0].id : null
            };
            showAddModal.value = true;
        };

        const openEditModal = (t) => {
            isEditing.value = true;
            editingId.value = t.id;
            newForm.value = {
                type: t.type,
                amount: t.amount,
                date: t.date,
                description: t.description,
                category_id: t.category_id
            };
            showAddModal.value = true;
        };

        const fetchTransactions = async () => {
            try {
                const res = await axios.get('/api/transactions/', {
                    params: {
                        page: currentPage.value,
                        search: searchQuery.value
                    }
                });
                transactions.value = res.data.transactions;
                totalPages.value = res.data.pages;
                currentPage.value = res.data.current_page;
            } catch (e) {
                console.error(e);
            }
        };

        const fetchCategories = async () => {
            try {
                const res = await axios.get('/api/categories/');
                categories.value = res.data;
                if (categories.value.length > 0) {
                    newForm.value.category_id = categories.value[0].id;
                }
            } catch (e) {
                console.error(e);
            }
        };

        const debouncedSearch = _.debounce(() => {
            currentPage.value = 1;
            fetchTransactions();
        }, 300);

        const submitTransaction = async () => {
            try {
                if (isEditing.value) {
                    await axios.put(`/api/transactions/${editingId.value}`, newForm.value);
                } else {
                    await axios.post('/api/transactions/', newForm.value);
                }
                showAddModal.value = false;
                fetchTransactions();
            } catch (e) {
                alert("Error saving transaction");
                console.error(e);
            }
        };

        const deleteTransaction = async (id) => {
            if (!confirm("Are you sure?")) return;
            try {
                await axios.delete(`/api/transactions/${id}`);
                fetchTransactions();
            } catch (e) {
                console.error(e);
            }
        };

        const nextPage = () => {
            if (currentPage.value < totalPages.value) {
                currentPage.value++;
            }
        };

        const prevPage = () => {
            if (currentPage.value > 1) {
                currentPage.value--;
            }
        };

        watch(currentPage, fetchTransactions);

        onMounted(() => {
            fetchTransactions();
            fetchCategories();
        });

        return {
            transactions, searchQuery, currentPage, totalPages,
            showAddModal, isEditing, newForm, categories,
            debouncedSearch, submitTransaction, deleteTransaction,
            openAddModal, openEditModal,
            nextPage, prevPage
        };
    }
};

// --- Budgets Component ---
const BudgetsView = {
    template: `
        <div>
            <div style="display: flex; justify-content: space-between; align-items: center; margin-bottom: 20px;">
                <h2>Monthly Budgets</h2>
                <button @click="showSetModal = true">⚙️ Set Limits</button>
            </div>

            <div class="grid">
                <div v-for="b in budgets" :key="b.id" class="card">
                    <div style="display: flex; justify-content: space-between;">
                        <div>
                            <h3 style="margin-bottom: 5px;">
                                <span :style="{color: b.category_color}">🏷️</span> {{ b.category_name }}
                            </h3>
                            <span style="font-size: 0.8em; color: #666;">{{ getMonthName(b.month) }} {{ b.year }}</span>
                        </div>
                        <div style="text-align: right;">
                            <div>Left</div>
                            <strong :class="(b.monthly_limit - b.spent) < 0 ? 'text-red' : 'text-green'">
                                €{{ (b.monthly_limit - b.spent).toFixed(2)}}
                            </strong>
                        </div>
                    </div>
                    
                    <div style="margin-top: 15px; font-size: 0.9em;">
                        <strong>€{{ b.spent.toFixed(2) }} spent</strong> of €{{ b.monthly_limit.toFixed(2) }}
                    </div>
                    
                    <div class="progress-container">
                        <div class="progress-bar"
                             :style="{ width: Math.min(b.burn_rate, 100) + '%', backgroundColor: getProgressColor(b.burn_rate) }">
                        </div>
                    </div>

                    <div v-if="b.burn_rate > 90" class="text-red mt-2 text-sm">
                        ⚠️ Critical: Over 90% spent!
                    </div>
                </div>

                <div v-if="budgets.length === 0" style="width: 100%; text-align: center; padding: 30px; color: #666;">
                    No budgets set for this month. Click "Set Limits" to get started.
                </div>
            </div>

            <!-- Set Budget Modal -->
            <div v-if="showSetModal" class="modal-overlay">
                <div class="modal">
                    <div class="modal-header">
                        <h2>Set Budget Limit</h2>
                        <button @click="showSetModal = false" class="close-btn">❌</button>
                    </div>

                    <div class="modal-content">
                        <div class="form-group">
                            <label>Category</label>
                            <select v-model="budgetForm.category_id" style="width: 100%;">
                                <option v-for="c in categories" :key="c.id" :value="c.id">{{ c.name }}</option>
                            </select>
                        </div>

                        <div class="form-group">
                            <label>Monthly Limit (€)</label>
                            <input v-model.number="budgetForm.monthly_limit" type="number" step="10" style="width: 100%;">
                        </div>
                        
                        <div style="margin-top: 20px; text-align: right;">
                            <button @click="saveBudget">💾 Save</button>
                        </div>
                    </div>
                </div>
            </div>
        </div>
    `,
    setup() {
        const budgets = ref([]);
        const showSetModal = ref(false);
        const categories = ref([]);
        const budgetForm = ref({
            category_id: null,
            monthly_limit: 500
        });

        const fetchBudgets = async () => {
            try {
                const res = await axios.get('/api/budgets/');
                budgets.value = res.data;
            } catch (e) { console.error(e); }
        };

        const fetchCategories = async () => {
            try {
                const res = await axios.get('/api/categories/');
                categories.value = res.data;
                if (categories.value.length > 0) budgetForm.value.category_id = categories.value[0].id;
            } catch (e) { console.error(e); }
        };

        const saveBudget = async () => {
            try {
                await axios.post('/api/budgets/', budgetForm.value);
                showSetModal.value = false;
                fetchBudgets();
            } catch (e) { alert("Error saving budget"); }
        };

        const getProgressColor = (rate) => {
            if (rate > 85) return '#EF4444'; // Red
            if (rate > 50) return '#F59E0B'; // Yellow
            return '#10B981'; // Green
        };

        const getMonthName = (m) => {
            return new Date(0, m - 1).toLocaleString('default', { month: 'long' });
        };

        onMounted(() => {
            fetchBudgets();
            fetchCategories();
        });

        return { budgets, showSetModal, budgetForm, categories, saveBudget, getProgressColor, getMonthName };
    }
};

// --- Main App ---
const app = createApp({
    setup() {
        const currentView = ref('dashboard');
        const showExportModal = ref(false);
        const exportForm = ref({
            month: new Date().getMonth() + 1,
            year: new Date().getFullYear()
        });

        const exportJson = () => {
            window.location.href = '/api/export/json';
            showExportModal.value = false;
        };

        const exportPdf = () => {
            const { month, year } = exportForm.value;
            window.location.href = `/api/export/pdf?month=${month}&year=${year}`;
            showExportModal.value = false;
        };

        return { currentView, showExportModal, exportForm, exportJson, exportPdf };
    }
});

// Register Components
app.component('dashboard-view', DashboardView);
app.component('transactions-view', TransactionsView);
app.component('budgets-view', BudgetsView);

// Mount
app.mount('#app');
