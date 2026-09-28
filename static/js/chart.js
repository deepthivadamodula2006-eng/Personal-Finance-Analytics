document.addEventListener("DOMContentLoaded", function () {

    const data = window.financeData;

    const expenseData = data.expenseData || {};

    const categories = Object.keys(expenseData);

    const amounts = Object.values(expenseData).map(
        value => Number(value) || 0
    );

    // =====================================================
    // 1. FINANCIAL HEALTH SCORE
    // =====================================================

    const scoreCanvas = document.getElementById("scoreChart");

    if (scoreCanvas) {

        new Chart(scoreCanvas, {

            type: "doughnut",

            data: {
                labels: [
                    "Score",
                    "Remaining"
                ],

                datasets: [{
                    data: [
                        data.score,
                        Math.max(100 - data.score, 0)
                    ]
                }]
            },

            options: {
                responsive: true,
                maintainAspectRatio: false,

                plugins: {
                    legend: {
                        position: "bottom"
                    }
                }
            }

        });

    }


    // =====================================================
    // 2. INCOME VS EXPENSES VS SAVINGS
    // =====================================================

    const moneyCanvas = document.getElementById("moneyChart");

    if (moneyCanvas) {

        new Chart(moneyCanvas, {

            type: "bar",

            data: {

                labels: [
                    "Income",
                    "Expenses",
                    "Savings"
                ],

                datasets: [{
                    label: "Amount (₹)",

                    data: [
                        data.income,
                        data.expenses,
                        data.savings
                    ]
                }]

            },

            options: {

                responsive: true,
                maintainAspectRatio: false,

                scales: {

                    y: {
                        beginAtZero: true,

                        ticks: {
                            callback: function (value) {
                                return "₹ " + value;
                            }
                        }
                    }

                },

                plugins: {

                    legend: {
                        display: false
                    }

                }

            }

        });

    }


    // =====================================================
    // 3. EXPENSE DISTRIBUTION
    // =====================================================

    const pieCanvas = document.getElementById("expensePie");

    if (pieCanvas) {

        new Chart(pieCanvas, {

            type: "pie",

            data: {

                labels: categories,

                datasets: [{
                    label: "Expense Distribution",
                    data: amounts
                }]

            },

            options: {

                responsive: true,
                maintainAspectRatio: false,

                plugins: {

                    legend: {
                        position: "bottom"
                    },

                    tooltip: {

                        callbacks: {

                            label: function (context) {

                                return context.label +
                                    ": ₹ " +
                                    context.raw;

                            }

                        }

                    }

                }

            }

        });

    }


    // =====================================================
    // 4. BUDGET UTILIZATION
    // =====================================================

    const budgetCanvas = document.getElementById("budgetChart");

    if (budgetCanvas) {

        new Chart(budgetCanvas, {

            type: "doughnut",

            data: {

                labels: [
                    "Used",
                    "Remaining"
                ],

                datasets: [{

                    data: [
                        data.budgetUsed,
                        Math.max(100 - data.budgetUsed, 0)
                    ]

                }]

            },

            options: {

                responsive: true,
                maintainAspectRatio: false,

                plugins: {

                    legend: {
                        position: "bottom"
                    }

                }

            }

        });

    }

// =====================================================
// 5. SAVINGS VS SPENDING ANALYSIS
// HORIZONTAL BAR CHART
// =====================================================

const expenseBarCanvas =
    document.getElementById("expenseBar");

if (expenseBarCanvas) {

    new Chart(expenseBarCanvas, {

        type: "bar",

        data: {

            labels: [

                "Monthly Income",

                "Total Expenses",

                "Current Savings",

                "Savings Goal"

            ],

            datasets: [{

                label: "Amount (₹)",

                data: [

                    Number(data.income) || 0,

                    Number(data.expenses) || 0,

                    Number(data.currentSavings) || 0,

                    Number(data.savingsGoal) || 0

                ]

            }]

        },

        options: {

            indexAxis: "y",

            responsive: true,

            maintainAspectRatio: false,

            scales: {

                x: {

                    beginAtZero: true,

                    ticks: {

                        callback: function (value) {

                            return "₹ " + value;

                        }

                    }

                }

            },

            plugins: {

                legend: {

                    display: false

                },

                tooltip: {

                    callbacks: {

                        label: function (context) {

                            return "₹ " + context.raw;

                        }

                    }

                }

            }

        }

    });

}

});