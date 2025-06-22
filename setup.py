from setuptools import setup, find_packages

with open("README.md", "r", encoding="utf-8") as fh:
    long_description = fh.read()

setup(
    name="vessel-tool",
    version="1.0.0",
    author="Vessel Tool Team",
    author_email="chenxr93@163.com",
    description="肝脏血管三维重建与可视化工具",
    long_description=long_description,
    long_description_content_type="text/markdown",
    url="https://github.com/yourusername/vessel-tool",
    packages=find_packages(),
    classifiers=[
        "Development Status :: 4 - Beta",
        "Intended Audience :: Healthcare Industry",
        "License :: OSI Approved :: MIT License",
        "Operating System :: OS Independent",
        "Programming Language :: Python :: 3",
        "Programming Language :: Python :: 3.7",
        "Programming Language :: Python :: 3.8",
        "Programming Language :: Python :: 3.9",
        "Topic :: Scientific/Engineering :: Medical Science Apps.",
    ],
    python_requires=">=3.7",
    install_requires=[
        "numpy>=1.19.0",
        "scipy>=1.5.0",
        "matplotlib>=3.3.0",
        "scikit-image>=0.17.0",
        "scikit-learn>=0.23.0",
        "open3d>=0.12.0",
        "vtk>=9.0.0",
        "pyvista>=0.30.0",
        "SimpleITK>=2.0.0",
        "pydicom>=2.0.0",
        "nibabel>=3.2.0",
        "pynrrd>=0.4.0",
        "pillow>=8.0.0",
        "numpy-stl>=2.16.0",
    ],
    extras_require={
        "dev": [
            "pytest>=6.0",
            "pytest-cov>=2.10",
            "black>=21.0",
            "flake8>=3.8",
            "mypy>=0.800",
        ],
    },
) 