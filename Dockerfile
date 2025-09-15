# GRDB.swift Test Environment Dockerfile
#
# This Dockerfile creates a Linux environment for building and testing
# the GRDB.swift package. It's optimized for CI/CD and includes all
# necessary tools for testing and reporting.

FROM swift:6.1-noble

# Set environment variables
ENV DEBIAN_FRONTEND=noninteractive
ENV LANG=C.UTF-8
ENV LC_ALL=C.UTF-8

# Install system dependencies
RUN apt-get update && apt-get install -y \
    # Basic tools
    curl \
    git \
    unzip \
    wget \
    # Python for test script
    python3 \
    python3-pip \
    # Build tools
    build-essential \
    pkg-config \
    # LLVM tools for coverage
    llvm \
    llvm-dev \
    # SQLite development
    libsqlite3-dev \
    # SSL support
    libssl-dev \
    # Cleanup
    && rm -rf /var/lib/apt/lists/*

# Create a patch for CoreGraphics dependency in tests
RUN mkdir -p /patches

# Set library path environment variables for Swift build
ENV PKG_CONFIG_PATH="/usr/local/lib/pkgconfig:/usr/lib/pkgconfig:/usr/share/pkgconfig:$PKG_CONFIG_PATH"
ENV LD_LIBRARY_PATH="/usr/local/lib:/usr/lib:$LD_LIBRARY_PATH"
ENV LIBRARY_PATH="/usr/local/lib:/usr/lib:$LIBRARY_PATH"
ENV C_INCLUDE_PATH="/usr/local/include:/usr/include:$C_INCLUDE_PATH"
ENV CPLUS_INCLUDE_PATH="/usr/local/include:/usr/include:$CPLUS_INCLUDE_PATH"

# Create a symbolic link for python3 as python
RUN ln -sf /usr/bin/python3 /usr/bin/python

# Verify installations
RUN swift --version && \
    python3 --version && \
    llvm-config --version

# Set working directory
WORKDIR /workspace

# Create reports directory
RUN mkdir -p reports

# Default command - will be overridden by docker-compose
CMD ["bash"]