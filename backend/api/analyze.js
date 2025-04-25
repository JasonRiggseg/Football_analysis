const fs = require('fs');
const path = require('path');
const { exec } = require('child_process');

// Directory to store the uploaded videos and outputs
const UPLOAD_DIR = '/tmp/uploads';
const OUTPUT_DIR = '/tmp/outputs';

module.exports = async (req, res) => {
  // Check if the request is a POST request
  if (req.method === 'POST') {
    // Handle file upload
    const file = req.files.file;

    // Ensure directories exist (Vercel uses the /tmp directory for local file storage)
    if (!fs.existsSync(UPLOAD_DIR)) {
      fs.mkdirSync(UPLOAD_DIR, { recursive: true });
    }
    if (!fs.existsSync(OUTPUT_DIR)) {
      fs.mkdirSync(OUTPUT_DIR, { recursive: true });
    }

    // Save the uploaded file
    const filePath = path.join(UPLOAD_DIR, file.name);
    await file.mv(filePath);

    // Perform the analysis (this could be a custom script or call to an AI model)
    const outputPath = path.join(OUTPUT_DIR, 'analysis_result.mp4');
    try {
      // Assume the analysis script generates a result at outputPath
      exec(`python analyze.py ${filePath} ${outputPath}`, (error, stdout, stderr) => {
        if (error) {
          console.error(`Error executing analysis: ${stderr}`);
          res.status(500).send('Error during analysis');
          return;
        }

        // Send the result video back
        res.setHeader('Content-Type', 'video/mp4');
        res.setHeader('Content-Disposition', 'attachment; filename=analysis_result.mp4');
        res.sendFile(outputPath);
      });
    } catch (error) {
      console.error(error);
      res.status(500).send('Server error during analysis');
    }
  } else {
    // Handle any non-POST requests
    res.status(405).send('Method Not Allowed');
  }
};
