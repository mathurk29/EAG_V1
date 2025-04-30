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
    resultDiv.innerHTML = `
      <h3>Analysis Results</h3>
      <p>Stock: ${stockName}</p>
      <p>Status: ${data.status}</p>
      <p>Message: ${data.message}</p>
    `;
  } catch (error) {
    resultDiv.textContent = `Error: ${error.message}`;
  }
}); 