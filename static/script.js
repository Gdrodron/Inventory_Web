document.addEventListener("DOMContentLoaded", function () {

    // =========================
    // DATA
    // =========================
    let labels = JSON.parse(document.getElementById("chart-labels")?.textContent || "[]");
    let data = JSON.parse(document.getElementById("chart-data")?.textContent || "[]");

    // =========================
    // TOP 5 ONLY
    // =========================
    let combined = labels.map((label, i) => ({
        label: label,
        value: data[i]
    }));

    combined.sort((a, b) => b.value - a.value);
    combined = combined.slice(0, 5);

    labels = combined.map(item => item.label);
    data = combined.map(item => item.value);

    // =========================
    // CHART
    // =========================
    const canvas = document.getElementById("productChart");
    const loader = document.getElementById("chartLoading");

    if (canvas) {

        canvas.style.opacity = 0;

        new Chart(canvas, {
            type: "bar",
            data: {
                labels: labels,
                datasets: [{
                    label: "Top Products Stock",
                    data: data,
                    backgroundColor: "rgba(59, 130, 246, 0.6)",
                    borderRadius: 6
                }]
            },
            options: {
                indexAxis: "y",
                responsive: true,
                maintainAspectRatio: false,
                scales: {
                    x: {
                        beginAtZero: true,
                        suggestedMax: Math.max(...data) + 10
                    },
                    y: {
                        grid: {
                            display: false
                        }
                    }
                }
            }
        });
        if (loader) {
            setTimeout(() => {
                loader.style.opacity = "0";

                setTimeout(() => {
                    loader.style.display = "none";
                    canvas.style.transition = "opacity 0.5s ease";
                    canvas.style.opacity = "1";
                }, 300);

            }, 400);
        }
    }

    // =========================
    // COUNTERS
    // =========================
    document.querySelectorAll(".counter").forEach(counter => {

        let target = parseInt(counter.getAttribute("data-target")) || 0;
        let current = 0;

        let step = Math.ceil(target / 40);

        let interval = setInterval(() => {
            current += step;

            if (current >= target) {
                counter.innerText = target;
                clearInterval(interval);
            } else {
                counter.innerText = current;
            }
        }, 20);
    });

});

// =========================
// IMAGE MODAL
// =========================
function openImage(src) {
    const modal = document.getElementById("imgModal");
    const img = document.getElementById("modalImg");

    if (modal && img) {
        modal.style.display = "flex";
        img.src = src;
    }
}

function closeImage() {
    const modal = document.getElementById("imgModal");
    if (modal) {
        modal.style.display = "none";
    }
}