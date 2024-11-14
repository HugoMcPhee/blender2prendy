#!/usr/bin/env node

const { execSync } = require("child_process");
const { existsSync, mkdirSync, writeFileSync, readdirSync } = require("fs");
const { join, basename, extname } = require("path");
const argv = require("yargs")
  .usage("Usage: $0 -i [input HDR file] [-o [output KTX2 file]]")
  .demandOption(["i"])
  .alias("i", "input")
  .alias("o", "output")
  .describe("i", "Input HDR file")
  .describe("o", "Output KTX2 file (optional)").argv;

// Extract input and output file paths from command-line arguments
const inputHDR = argv.input;
let outputKTX2 = argv.output;

// If output file is not specified, use input filename with .ktx2 extension
if (!outputKTX2) {
  const inputBaseName = basename(inputHDR, extname(inputHDR));
  outputKTX2 = `${inputBaseName}.ktx2`;
}

// Ensure cmgen and toktx are available
function checkCommand(cmd) {
  try {
    execSync(`which ${cmd}`);
  } catch (err) {
    console.error(`Error: ${cmd} is not installed or not in PATH.`);
    process.exit(1);
  }
}

checkCommand("cmgen");
checkCommand("toktx");

// Create a temporary directory for output
const outputDir = "cmgen_output";
if (!existsSync(outputDir)) {
  mkdirSync(outputDir);
}

// Step 1: Run cmgen to generate prefiltered environment map in PNG format
console.log("Running cmgen...");
try {
  execSync(`cmgen --format=png --size=256 --deploy=${outputDir} ${inputHDR}`, {
    stdio: "inherit",
  });
} catch (err) {
  console.error("Error running cmgen:", err);
  process.exit(1);
}

// Since cmgen creates a subdirectory named after the input HDR file (without extension), adjust paths accordingly
const hdrBaseName = basename(inputHDR, extname(inputHDR));
const iblDir = join(outputDir, hdrBaseName);

// Check if the iblDir exists
if (!existsSync(iblDir)) {
  console.error(`Error: Expected directory not found at ${iblDir}`);
  process.exit(1);
}

// Step 2: Prepare the list of images for toktx
// Get a list of all files in the iblDir
const files = readdirSync(iblDir);

// Filter out only the image files
const imageFiles = files.filter((name) => name.endsWith(".png"));

// Group images by face and mip level
const faceMipLevels = {};

// Regular expression to match the filenames
// Only include images with mip level prefix: m{level}_{face}.png
const mipFaceRegex = /^m(\d+)_([np][xyz])\.png$/;

for (const fileName of imageFiles) {
  const match = fileName.match(mipFaceRegex);
  if (match) {
    const mipLevelStr = match[1];
    const face = match[2];
    const mipLevel = parseInt(mipLevelStr, 10);
    if (!faceMipLevels[face]) {
      faceMipLevels[face] = {};
    }
    faceMipLevels[face][mipLevel] = join(iblDir, fileName);
  }
}

// Ensure all faces have the same number of mip levels
const faces = ["px", "nx", "py", "ny", "pz", "nz"];
let numMipLevels = null;
for (const face of faces) {
  const mipLevels = faceMipLevels[face];
  if (!mipLevels) {
    console.error(`Missing images for face ${face}`);
    process.exit(1);
  }
  const mipLevelKeys = Object.keys(mipLevels)
    .map(Number)
    .sort((a, b) => a - b);

  console.log("mipLevelKeys");
  console.log(mipLevelKeys);

  if (numMipLevels === null) {
    numMipLevels = mipLevelKeys.length;
  } else if (numMipLevels !== mipLevelKeys.length) {
    console.error(`Inconsistent number of mip levels for face ${face}`);
    process.exit(1);
  }
}

// Get sorted mip levels (from largest to smallest)
const sortedMipLevels = [];
for (let i = 0; i < numMipLevels; i++) {
  sortedMipLevels.push(i);
}

// Prepare an array to hold the image file paths in the correct order
// Order: for each face, for each mip level
const imageList = [];

for (const face of faces) {
  for (const mipLevel of sortedMipLevels) {
    const imagePath = faceMipLevels[face][mipLevel];
    if (!imagePath || !existsSync(imagePath)) {
      console.error(
        `Missing image file for face ${face}, mip level ${mipLevel}`
      );
      process.exit(1);
    }
    imageList.push(imagePath);
  }
}

console.log("imageList");
console.log(imageList);

// Write the image list to a temporary text file
const imageListFile = "cubemap_images.txt";
writeFileSync(imageListFile, imageList.join("\n"));

// Step 3: Use toktx to create the KTX2 cubemap
console.log("Running toktx...");
try {
  execSync(
    `toktx --t2 --uastc 2 --zcmp 18 --cubemap --layers 1 --mipmap ${outputKTX2} @${imageListFile}`,
    { stdio: "inherit" }
  );
} catch (err) {
  console.error("Error running toktx:", err);
  process.exit(1);
}

// Clean up temporary files
console.log("Cleaning up temporary files...");
try {
  // Remove the temporary image list file
  execSync(`rm ${imageListFile}`);
  // Optionally, remove the output directory from cmgen
  // Comment out the next line if you want to keep the cmgen output
  execSync(`rm -rf ${outputDir}`);
} catch (err) {
  console.error("Error cleaning up temporary files:", err);
}

console.log(`Successfully created ${outputKTX2}`);
