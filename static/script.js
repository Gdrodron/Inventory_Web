document.addEventListener("DOMContentLoaded", function () {

    // =========================
    // CHART
    // =========================
    const labels = JSON.parse(document.getElementById("chart-labels").textContent);
    const data = JSON.parse(document.getElementById("chart-data").textContent);

    const canvas = document.getElementById("productChart");
    const loader = document.getElementById("chartLoading");

    canvas.style.opacity = 0;

    new Chart(canvas, {
        type: "bar",
        data: {
            labels: labels,
            datasets: [{
                label: "Products",
                data: data,
                backgroundColor: "rgba(59, 130, 246, 0.6)",
                borderRadius: 6
            }]
        },
        options: {
            responsive: true,
            animation: {
                duration: 900
            }
        }
    });

    setTimeout(() => {
        loader.style.opacity = 0;

        setTimeout(() => {
            loader.style.display = "none";
            canvas.style.transition = "opacity 0.5s ease";
            canvas.style.opacity = 1;
        }, 300);

    }, 400);

    // =========================
    // COUNTERS
    // =========================
    const counters = document.querySelectorAll(".counter");

    counters.forEach(counter => {
        counter.innerText = "0";

        const updateCounter = () => {
            const target = +counter.getAttribute("data-target");
            const current = +counter.innerText;

            const increment = Math.ceil(target / 30);

            if (current < target) {
                counter.innerText = current + increment;
                setTimeout(updateCounter, 30);
            } else {
                counter.innerText = target;
            }
        };

        updateCounter();
    });

});