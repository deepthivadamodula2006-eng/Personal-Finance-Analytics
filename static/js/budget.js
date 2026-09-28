// =====================================
// Personal Finance Management
// budget.js
// =====================================

document.addEventListener("DOMContentLoaded", function () {

    const incomeInput = document.getElementById("income");
    const expenseInput = document.getElementById("expenses");

    const calculateBtn = document.getElementById("calculateBtn");
    const resetBtn = document.getElementById("resetBtn");

    const savingsOutput = document.getElementById("savings");
    const remainingOutput = document.getElementById("remaining");
    const percentageOutput = document.getElementById("percentage");
    const statusOutput = document.getElementById("status");

    // ============================
    // Calculate Budget
    // ============================

    if (calculateBtn) {

        calculateBtn.addEventListener("click", function () {

            const income = parseFloat(incomeInput.value) || 0;
            const expenses = parseFloat(expenseInput.value) || 0;

            if (income <= 0) {
                alert("Please enter a valid income.");
                return;
            }

            if (expenses < 0) {
                alert("Expenses cannot be negative.");
                return;
            }

            const savings = income - expenses;
            const spentPercent = ((expenses / income) * 100).toFixed(2);

            savingsOutput.innerHTML = "₹ " + savings.toFixed(2);
            remainingOutput.innerHTML = "₹ " + savings.toFixed(2);
            percentageOutput.innerHTML = spentPercent + "%";

            if (spentPercent <= 50) {

                statusOutput.innerHTML = "🟢 Excellent Budget Management";

            }
            else if (spentPercent <= 75) {

                statusOutput.innerHTML = "🟡 Good Budget Management";

            }
            else if (spentPercent <= 90) {

                statusOutput.innerHTML = "🟠 Reduce Your Expenses";

            }
            else {

                statusOutput.innerHTML = "🔴 Budget Exceeded";

            }

        });

    }

    // ============================
    // Reset Fields
    // ============================

    if (resetBtn) {

        resetBtn.addEventListener("click", function () {

            incomeInput.value = "";
            expenseInput.value = "";

            savingsOutput.innerHTML = "₹ 0";
            remainingOutput.innerHTML = "₹ 0";
            percentageOutput.innerHTML = "0%";
            statusOutput.innerHTML = "-";

        });

    }

});