import fs from "fs";
import path from "path";
import sharp from "sharp";
import pngquant from "pngquant-bin";
import { spawn } from "child_process";

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

function generateNoiseImage(width, height) {
  const noise = Buffer.alloc(width * height * 4);

  for (let i = 0; i < noise.length; i += 4) {
    const offset = 2;
    const min = 128 - offset; // Minimum value for noise
    const max = 128 + offset; // Maximum value for noise
    const value = Math.floor(Math.random() * (max - min + 1)) + min;
    const alphaValue = Math.floor(Math.random() * 256);
    noise[i] = value; // Red
    noise[i + 1] = value; // Green
    noise[i + 2] = value; // Blue
    noise[i + 3] = 255; // Alpha (adjust for transparency)
  }

  return sharp(noise, {
    raw: {
      width: width,
      height: height,
      channels: 4,
    },
  });
}
async function addNoiseOverlay(inputImagePath, outputImagePath) {
  const { width, height } = await sharp(inputImagePath).metadata();

  const noiseImage = generateNoiseImage(width, height);

  // Encode the noise image as PNG
  const noiseBuffer = await noiseImage.png().toBuffer();

  await sharp(inputImagePath)
    .composite([{ input: noiseBuffer, blend: "overlay" }])
    .toFile(outputImagePath);
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

// Get depth argument
// const depth = process.argv.includes("--depth");

// Async function to process batches
(async () => {
  // Break frames into batches
  let textureCount = 0;
  while (frameFiles.length > 0) {
    textureCount++;
    const batchFrames = frameFiles.splice(0, framesPerTexture);
    const frameCount = batchFrames.length;

    // Calculate rows and columns
    const cols = Math.min(columns, frameCount);
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
    try {
      const data = await sharp({
        create: {
          width: outputWidth,
          height: outputHeight,
          channels: 4,
          background: { r: 0, g: 0, b: 0, alpha: 0 }, // Transparent background
        },
      })
        .composite(composites)
        .png()
        .toBuffer();

      const tempFile = path.join(outputDir, `temp_texture${textureCount}.png`);
      const outputFile = path.join(outputDir, `texture${textureCount}.png`);

      fs.writeFileSync(tempFile, data);

      // Add noise overlay
      await addNoiseOverlay(tempFile, outputFile);

      // if (depth) {
      //   // Use pngquant to reduce colors and apply dithering
      //   await new Promise((resolve, reject) => {
      //     const pngquantProcess = spawn(pngquant, [
      //       "16", // Number of colors
      //       "--quality=50-100",
      //       "--speed=1",
      //       "--force",
      //       "--output",
      //       outputFile,
      //       tempFile,
      //     ]);

      //     let stderr = "";

      //     pngquantProcess.stderr.on("data", (data) => {
      //       stderr += data.toString();
      //     });

      //     pngquantProcess.on("close", (code) => {
      //       fs.unlinkSync(tempFile); // Remove temp file
      //       if (code === 0) {
      //         console.log(
      //           `Created ${outputFile} with dimensions ${outputWidth}x${outputHeight}`
      //         );
      //         resolve();
      //       } else {
      //         console.error(`pngquant process exited with code ${code}`);
      //         console.error(`pngquant stderr: ${stderr}`);
      //         reject(new Error(`pngquant exited with code ${code}`));
      //       }
      //     });

      //     pngquantProcess.on("error", (err) => {
      //       fs.unlinkSync(tempFile); // Remove temp file
      //       reject(err);
      //     });
      //   });

      //   // Optimize the image using sharp, turn it back into an 16 bit image
      //   const optimizedData = await sharp(outputFile)
      //     .png({ quality: 100, compressionLevel: 9 })
      //     .toBuffer();
      //   fs.writeFileSync(outputFile, optimizedData);
      // } else {
      // Save the image without using pngquant
      // fs.renameSync(tempFile, outputFile);
      console.log(
        `Created ${outputFile} with dimensions ${outputWidth}x${outputHeight}`
      );
      // }
    } catch (err) {
      console.error("Error creating composite image:", err);
    }
  }
})();
