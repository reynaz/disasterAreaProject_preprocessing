# LiDAR Data Preprocessing Pipeline

This repository contains the preprocessing stage of a LiDAR-based 3D data pipeline.  
The focus of this project is transforming raw LiDAR point cloud data into structured, analysis-ready formats using Python.

This work was done as part of a larger LiDAR processing workflow and is separated into two repositories to keep preprocessing and downstream modeling clearly isolated.

---

## What This Project Does

Raw LiDAR data is powerful but messy.  
This pipeline takes unstructured point cloud data and progressively refines it through multiple geometric and spatial processing steps.

The preprocessing flow includes:

- Unit normalization and coordinate transformations  
- Spatial tiling to handle large-scale point clouds efficiently  
- Ground filtering using CSF (Cloth Simulation Filtering)  
- Surface reconstruction preparation using Delaunay triangulation  

The goal is to produce clean, structured data that can be reliably used in further 3D modeling, analysis, or visualization stages.

---

## Processing Steps

### 1. Unit Conversion & Normalization
Raw LiDAR datasets often come with inconsistent units and coordinate systems.  
This step ensures:
- Consistent measurement units
- Aligned coordinate reference
- Clean numerical stability for downstream geometry operations

---

### 2. Tiling
Large point clouds are split into smaller spatial tiles to:
- Reduce memory usage
- Enable parallel or batch processing
- Improve performance of filtering and triangulation algorithms

This step is essential for scalability when working with real-world LiDAR datasets.

---

### 3. CSF – Cloth Simulation Filtering
CSF is used to separate ground points from non-ground points.

In this stage:
- A simulated cloth model is applied over the inverted point cloud
- Ground points are extracted based on cloth deformation
- Non-ground objects (vegetation, buildings, noise) are filtered out

This produces a much cleaner ground surface representation.

---

### 4. Delaunay Preparation
After filtering, the remaining point cloud is prepared for surface reconstruction.

- Points are structured for Delaunay triangulation
- Ensures geometric consistency
- Enables later mesh or terrain modeling steps

---

## Technologies Used

- **Python**
- NumPy
- tensorflow
- Open3D
- Pdal
- Laspy
- SciPy
- LiDAR / point cloud processing libraries
- Computational geometry techniques

---

## Project Structure

