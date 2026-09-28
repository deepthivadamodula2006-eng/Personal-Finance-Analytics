document.addEventListener("DOMContentLoaded", function () {

    console.log("SCRIPT.JS IS LOADED");
    console.log("Finance Data:", window.financeData);

    const data = window.financeData;

    console.log("Finance Data:", data);

    // =========================================================
    // COMMON DATA
    // =========================================================

    const expenseData = data.expenseData || {};

    const categories = Object.keys(expenseData);

    const amounts = Object.values(expenseData).map(value =>
        Number(value) || 0
    );


    // =========================================================
    // 1. FINANCIAL HEALTH SCORE
    // =========================================================

    const scoreCanvas = document.getElementById("scoreChart");

    if (scoreCanvas) {

        new Chart(scoreCanvas, {

            type: "doughnut",

            data: {

                labels: [
                    "Financial Score",
                    "Remaining Score"
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


    // =========================================================
    // 2. INCOME VS EXPENSES VS SAVINGS
    // =========================================================

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


    // =========================================================
    // 3. EXPENSE DISTRIBUTION
    // =========================================================

    const pieCanvas = document.getElementById("expensePie");

    if (pieCanvas) {

        new Chart(pieCanvas, {

            type: "doughnut",

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

                                return (
                                    context.label +
                                    ": ₹ " +
                                    context.raw
                                );

                            }

                        }

                    }

                }

            }

        });

    }


    // =========================================================
    // 4. BUDGET UTILIZATION
    // =========================================================

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

                    },

                    tooltip: {

                        callbacks: {

                            label: function (context) {

                                return (
                                    context.label +
                                    ": " +
                                    context.raw.toFixed(2) +
                                    "%"
                                );

                            }

                        }

                    }

                }

            }

        });

    }


    // =========================================================
    // 5. EXPENSE CATEGORY ANALYSIS
    // HORIZONTAL BAR CHART
    // =========================================================

    const expenseBarCanvas =
        document.getElementById("expenseBar");

    if (expenseBarCanvas) {

        // Create sorted category data
        const sortedExpenses = categories
            .map((category, index) => ({
                category: category,
                amount: amounts[index]
            }))
            .sort((a, b) => b.amount - a.amount);


        const sortedCategories =
            sortedExpenses.map(item => item.category);

        const sortedAmounts =
            sortedExpenses.map(item => item.amount);


        new Chart(expenseBarCanvas, {

            type: "bar",

            data: {

                labels: sortedCategories,

                datasets: [{

                    label: "Expense Amount (₹)",

                    data: sortedAmounts

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

                        position: "bottom"

                    },

                    tooltip: {

                        callbacks: {

                            label: function (context) {

                                return (
                                    "₹ " +
                                    context.raw
                                );

                            }

                        }

                    }

                }

            }

        });

    }


    // =========================================================
    // 6. BUDGET VS ACTUAL SPENDING
    // GROUPED BAR CHART
    // =========================================================

    const performanceCanvas =
        document.getElementById("performanceChart");

    if (performanceCanvas) {

        new Chart(performanceCanvas, {

            type: "bar",

            data: {

                labels: [
                    "Monthly Budget",
                    "Actual Expenses",
                    "Remaining Budget"
                ],

                datasets: [{

                    label: "Amount (₹)",

                    data: [
                        data.budget,
                        data.expenses,
                        data.remaining
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

                        position: "bottom"

                    },

                    tooltip: {

                        callbacks: {

                            label: function (context) {

                                return (
                                    "₹ " +
                                    context.raw
                                );

                            }

                        }

                    }

                }

            }

        });

    }

});