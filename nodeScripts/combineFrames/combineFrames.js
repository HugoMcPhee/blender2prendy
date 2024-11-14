const fs = require("fs");
const path = require("path");
const sharp = require("sharp");

// Configuration
const framesDir = "./"; // Directory containing frame images
const outputDir = "./"; // Directory to save atlas images
const framesPerTexture = 16; // Max frames per texture image
const columns = 4; // Number of columns in the grid
const frameWidth = 2048; // Width of each frame
const frameHeight = 2048; // Height of each frame

// Ensure output directory exists
if (!fs.existsSync(outputDir)) {
  fs.mkdirSync(outputDir);
}

// Read and sort frame images
let frameFiles = fs
  .readdirSync(framesDir)
  .filter((file) => file.match(/^frame\d+\.png$/))
  .sort((a, b) => {
    const numA = parseInt(a.match(/^frame(\d+)\.png$/)[1], 10);
    const numB = parseInt(b.match(/^frame(\d+)\.png$/)[1], 10);
    return numA - numB;
  });

// Break frames into batches
let textureCount = 0;
while (frameFiles.length > 0) {
  textureCount++;
  const batchFrames = frameFiles.splice(0, framesPerTexture);
  const frameCount = batchFrames.length;

  // Calculate rows and columns
  const cols = columns;
  const rows = Math.ceil(frameCount / columns);

  // Calculate output image dimensions
  const outputWidth = frameWidth * cols;
  const outputHeight = frameHeight * rows;

  // Create an array of sharp images with metadata
  const composites = [];
  batchFrames.forEach((frame, index) => {
    const x = (index % columns) * frameWidth;
    const y = Math.floor(index / columns) * frameHeight;
    composites.push({
      input: path.join(framesDir, frame),
      top: y,
      left: x,
    });
  });

  // Create the composite image
  sharp({
    create: {
      width: outputWidth,
      height: outputHeight,
      channels: 4,
      background: { r: 0, g: 0, b: 0, alpha: 0 }, // Transparent background
    },
  })
    .composite(composites)
    .toFile(path.join(outputDir, `texture${textureCount}.png`))
    .then(() => {
      console.log(
        `Created texture${textureCount}.png with dimensions ${outputWidth}x${outputHeight}`
      );
    })
    .catch((err) => {
      console.error("Error creating texture image:", err);
    });
}
