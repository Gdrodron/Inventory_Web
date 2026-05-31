<>
  <script id="chart-labels" type="application/json">
    {JSON.stringify(products.map(product => product[1]))}
  </script>

  <script id="chart-data" type="application/json">
    {JSON.stringify(products.map(product => product[2]))}
  </script>

  <script src="https://cdn.jsdelivr.net/npm/chart.js"></script>
  <script src={urlForStatic('script.js')}></script>
</>