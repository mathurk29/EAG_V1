document.getElementById('analyze').addEventListener('click', async () => {
  const stockName = document.getElementById('stockName').value;
  const resultDiv = document.getElementById('result');
  
  if (!stockName) {
    resultDiv.textContent = 'Please enter a stock symbol';
    return;
  }

  resultDiv.textContent = 'Analyzing...';

  try {
    const response = await fetch('http://localhost:8000/analyze', {
      method: 'POST',
      headers: {
        'Content-Type': 'application/json',
      },
      body: JSON.stringify({ stock_name: stockName })
    });

    if (!response.ok) {
      throw new Error('Network response was not ok');
    }

    const data = await response.json();
    
    if (data.status === 'error') {
      resultDiv.innerHTML = `<p class="error">${data.message}</p>`;
      return;
    }

    // Create HTML content
    let htmlContent = `
      <h3>Analysis Results for ${stockName}</h3>
      <div class="graph-container">
        <img src="data:image/png;base64,${data.plot}" alt="Stock Price Graph" style="width: 100%;">
      </div>
      <div class="news-container">
        <h4>News Analysis</h4>
    `;

    // Add news summaries
    data.data.news.forEach((item, index) => {
      htmlContent += `
        <div class="news-item">
          <h5>${item.date}</h5>
          <p><strong>${item.title}</strong></p>
          <p>${item.summary}</p>
          <p>Price: $${data.data.prices[index].toFixed(2)}</p>
        </div>
      `;
    });

    htmlContent += '</div>';
    resultDiv.innerHTML = htmlContent;

  } catch (error) {
    resultDiv.textContent = `Error: ${error.message}`;
  }
}); 