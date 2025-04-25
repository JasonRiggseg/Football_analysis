import React, { useState } from 'react';

export default function HomePage() {
  const [file, setFile] = useState<File | null>(null);
  const [resultUrl, setResultUrl] = useState<string | null>(null);
  const [loading, setLoading] = useState(false);

  // ⚙️ Handles file selection
  const handleFileChange = (event: React.ChangeEvent<HTMLInputElement>) => {
    if (event.target.files && event.target.files[0]) {
      setFile(event.target.files[0]);
      setResultUrl(null); // Clear previous result when a new file is selected
    }
  };

  // 🚀 Sends file to backend and retrieves analysis result video
  const handleUpload = async () => {
    if (!file) return alert('Please select a file first.');
    setLoading(true);

    const formData = new FormData();
    formData.append('file', file); // 🔁 Ensure this key matches the backend expectations

    try {
      // Assuming your Vercel app is deployed at "https://your-vercel-deployment-url.vercel.app"
      const response = await fetch('football-analysis-nwaeb19qd-hala-abdeens-projects.vercel.app', {
        method: 'POST',
        body: formData,
      });

      if (!response.ok) {
        throw new Error(`Server error: ${response.statusText}`);
      }

      const blob = await response.blob();
      const url = URL.createObjectURL(blob);
      setResultUrl(url);
    } catch (error) {
      console.error(error);
      alert('Error during analysis');
    } finally {
      setLoading(false);
    }
  };

  return (
    <main className="min-h-screen bg-gray-900 text-white flex flex-col items-center justify-center p-6">
      <h1 className="text-4xl font-bold mb-4">🏈 Football Analysis</h1>
      <p className="mb-4 text-gray-400">Upload your match video to get player detection results</p>

      {/* Upload input */}
      <input
        type="file"
        accept="video/*"
        onChange={handleFileChange}
        className="mb-4 bg-gray-800 p-2 rounded border border-gray-700"
        title="Upload a video file"
      />

      {/* Show selected file */}
      {file && (
        <p className="mb-2 text-sm text-green-400">Selected: {file.name}</p>
      )}

      {/* Upload button */}
      <button
        onClick={handleUpload}
        disabled={loading}
        className="bg-green-500 hover:bg-green-600 text-white px-6 py-2 rounded"
      >
        {loading ? 'Analyzing...' : 'Show Analysis'}
      </button>

      {/* Result video display */}
      {resultUrl && (
        <div className="mt-6 bg-gray-800 p-4 rounded shadow-lg w-full max-w-md flex flex-col items-center">
          <h2 className="text-lg font-semibold mb-2">📊 Analysis Result Video</h2>
          <video controls src={resultUrl} className="w-full rounded" />
          <a href={resultUrl} download="analysis_result.mp4" className="mt-2 text-green-400 underline">
            Download Video
          </a>
        </div>
      )}
    </main>
  );
}
