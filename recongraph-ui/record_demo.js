const puppeteer = require('puppeteer');
const { PuppeteerScreenRecorder } = require('puppeteer-screen-recorder');

(async () => {
  console.log("Launching browser...");
  const browser = await puppeteer.launch({
    headless: "new",
    defaultViewport: { width: 1280, height: 800 }
  });
  
  const page = await browser.newPage();
  
  const recorder = new PuppeteerScreenRecorder(page);
  await recorder.start('recongraph_demo.mp4');
  console.log("Recording started: recongraph_demo.mp4");

  try {
    console.log("Navigating to http://localhost:3000...");
    await page.goto('http://localhost:3000', { waitUntil: 'networkidle0' });
    
    // Wait for the main screen to load
    await page.waitForSelector('button', { visible: true });
    
    console.log("Clicking 'Load Demo Dataset'...");
    // Find the load demo button by text
    const buttons = await page.$$('button');
    let loadBtn = null;
    for (const btn of buttons) {
      const text = await page.evaluate(el => el.textContent, btn);
      if (text.includes('Load Demo Dataset')) {
        loadBtn = btn;
        break;
      }
    }
    
    if (loadBtn) {
      await loadBtn.click();
      
      console.log("Waiting for Dashboard to load...");
      // Wait for the stat cards or Action Queue to appear
      await page.waitForSelector('table', { visible: true, timeout: 5000 });
      
      // Let the user view the dashboard for a few seconds
      await new Promise(r => setTimeout(r, 2000));
      
      console.log("Clicking a review packet...");
      // Click the first row in the table body
      const rows = await page.$$('tbody tr');
      if (rows.length > 0) {
        await rows[0].click();
        
        console.log("Viewing Packet Detail...");
        // Wait for the semantic findings to appear
        await page.waitForSelector('h2', { visible: true });
        
        // Let the user view the details for a few seconds
        await new Promise(r => setTimeout(r, 4000));
      }
    }
  } catch (err) {
    console.error("Error during recording:", err);
  } finally {
    console.log("Stopping recording...");
    await recorder.stop();
    await browser.close();
    console.log("Done! Video saved to recongraph_demo.mp4");
  }
})();
