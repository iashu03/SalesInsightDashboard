let monthlyRevenueChartInstance = null;
let categoryRevenueChartInstance = null;
let topCustomersChartInstance = null;
let topProductsChartInstance = null;

function formatIndianCurrency(value) {
    const number = Number(value || 0);
    return `₹ ${number.toLocaleString("en-IN", {
        maximumFractionDigits: 2
    })}`;
}

function formatIndianNumber(value) {
    const number = Number(value || 0);
    return number.toLocaleString("en-IN");
}

async function loadSummary() {
    try {
        const response = await fetch("/api/summary");
        const data = await response.json();

        const totalRevenue = document.getElementById("totalRevenue");
        const totalOrders = document.getElementById("totalOrders");
        const avgOrderValue = document.getElementById("avgOrderValue");
        const topProduct = document.getElementById("topProduct");
        const recentRecordsTable = document.getElementById("recentRecordsTable");

        if (totalRevenue) totalRevenue.textContent = formatIndianCurrency(data.total_revenue);
        if (totalOrders) totalOrders.textContent = formatIndianNumber(data.total_orders);
        if (avgOrderValue) avgOrderValue.textContent = formatIndianCurrency(data.avg_order_value);
        if (topProduct) topProduct.textContent = data.top_product;

        if (recentRecordsTable) {
            recentRecordsTable.innerHTML = "";

            if (!data.recent_records || data.recent_records.length === 0) {
                recentRecordsTable.innerHTML = `
                    <tr>
                        <td colspan="7" class="empty-state">No recent records available.</td>
                    </tr>
                `;
                return;
            }

            data.recent_records.forEach(row => {
                const tr = document.createElement("tr");
                tr.innerHTML = `
                    <td>${row.product_name}</td>
                    <td>${row.category_name}</td>
                    <td>${row.customer_name}</td>
                    <td>${formatIndianNumber(row.quantity)}</td>
                    <td>${formatIndianCurrency(row.price)}</td>
                    <td>${formatIndianCurrency(row.revenue)}</td>
                    <td>${row.order_date}</td>
                `;
                recentRecordsTable.appendChild(tr);
            });
        }
    } catch (error) {
        console.error("Summary error:", error);
    }
}

async function loadCharts() {
    try {
        const response = await fetch("/api/insights");
        const data = await response.json();

        const monthlyRevenueCanvas = document.getElementById("monthlyRevenueChart");
        const categoryRevenueCanvas = document.getElementById("categoryRevenueChart");
        const topCustomersCanvas = document.getElementById("topCustomersChart");
        const topProductsCanvas = document.getElementById("topProductsChart");

        if (monthlyRevenueCanvas) {
            if (monthlyRevenueChartInstance) monthlyRevenueChartInstance.destroy();

            monthlyRevenueChartInstance = new Chart(monthlyRevenueCanvas, {
                type: "bar",
                data: {
                    labels: data.monthly_sales.map(item => item.month),
                    datasets: [{
                        label: "Revenue",
                        data: data.monthly_sales.map(item => item.revenue),
                        backgroundColor: [
                            "rgba(37, 99, 235, 0.85)"
                        ],
                        borderRadius: 10
                    }]
                },
                options: {
                    responsive: true,
                    maintainAspectRatio: false,
                    plugins: {
                        legend: { display: false }
                    },
                    scales: {
                        y: {
                            ticks: {
                                callback: function(value) {
                                    return `₹ ${Number(value).toLocaleString("en-IN")}`;
                                }
                            }
                        }
                    }
                }
            });
        }

        if (categoryRevenueCanvas) {
            if (categoryRevenueChartInstance) categoryRevenueChartInstance.destroy();

            categoryRevenueChartInstance = new Chart(categoryRevenueCanvas, {
                type: "doughnut",
                data: {
                    labels: data.category_sales.map(item => item.category),
                    datasets: [{
                        data: data.category_sales.map(item => item.revenue),
                        backgroundColor: [
                            "#2563eb",
                            "#4f46e5",
                            "#06b6d4",
                            "#0f172a",
                            "#60a5fa"
                        ],
                        borderWidth: 2,
                        borderColor: "#ffffff"
                    }]
                },
                options: {
                    responsive: true,
                    maintainAspectRatio: false,
                    cutout: "55%"
                }
            });
        }

        if (topCustomersCanvas) {
            if (topCustomersChartInstance) topCustomersChartInstance.destroy();

            topCustomersChartInstance = new Chart(topCustomersCanvas, {
                type: "bar",
                data: {
                    labels: data.top_customers.map(item => item.customer_name),
                    datasets: [{
                        label: "Total Spent",
                        data: data.top_customers.map(item => item.total_spent),
                        backgroundColor: "rgba(79, 70, 229, 0.82)",
                        borderRadius: 10
                    }]
                },
                options: {
                    responsive: true,
                    maintainAspectRatio: false,
                    indexAxis: "y",
                    plugins: {
                        legend: { display: false }
                    },
                    scales: {
                        x: {
                            ticks: {
                                callback: function(value) {
                                    return `₹ ${Number(value).toLocaleString("en-IN")}`;
                                }
                            }
                        }
                    }
                }
            });
        }

        if (topProductsCanvas) {
            if (topProductsChartInstance) topProductsChartInstance.destroy();

            topProductsChartInstance = new Chart(topProductsCanvas, {
                type: "line",
                data: {
                    labels: data.top_products.map(item => item.product_name),
                    datasets: [{
                        label: "Quantity Sold",
                        data: data.top_products.map(item => item.total_quantity),
                        borderColor: "#06b6d4",
                        backgroundColor: "rgba(6, 182, 212, 0.15)",
                        fill: true,
                        tension: 0.35,
                        pointRadius: 4,
                        pointHoverRadius: 6
                    }]
                },
                options: {
                    responsive: true,
                    maintainAspectRatio: false
                }
            });
        }
    } catch (error) {
        console.error("Chart error:", error);
    }
}

function setupCategoryProductDropdown() {
    const categorySelect = document.getElementById("categorySelect");
    const productSelect = document.getElementById("productSelect");

    if (!categorySelect || !productSelect) return;

    productSelect.disabled = true;

    categorySelect.addEventListener("change", async function () {
        const categoryId = this.value;

        productSelect.innerHTML = '<option value="">Select Product</option>';
        productSelect.disabled = true;

        if (!categoryId) return;

        try {
            const response = await fetch(`/api/products-by-category/${categoryId}`);
            const products = await response.json();

            if (products.length === 0) {
                productSelect.innerHTML = '<option value="">No products available</option>';
                return;
            }

            products.forEach(product => {
                const option = document.createElement("option");
                option.value = product.id;
                option.textContent = product.name;
                productSelect.appendChild(option);
            });

            productSelect.disabled = false;
        } catch (error) {
            console.error("Product loading error:", error);
        }
    });
}

document.addEventListener("DOMContentLoaded", () => {
    loadSummary();
    loadCharts();
    setupCategoryProductDropdown();
});