# 第一阶段：基于官方 rust 镜像准备开发环境（包含 rustup/cargo）
FROM rust AS base
LABEL maintainer="kangzhehao <zhehaokang@hust.edu.cn>"

ENV RUSTUP_DIST_SERVER https://mirrors.tuna.tsinghua.edu.cn/rustup
ENV RUSTUP_UPDATE_ROOT https://mirrors.tuna.tsinghua.edu.cn/rustup/rustup

RUN rustup default stable && \
    rustup target add armv7a-none-eabi && \
    cargo install cargo-binutils && \
    rustup component add llvm-tools-preview && \
    rustup component add rust-src && \
    rustup component add rustfmt && \
    rustup component add clippy && \
    rustup component add rust-analyzer

# 确保 cargo/rustup 在 PATH
ENV PATH="${CARGO_HOME}/bin:/usr/local/bin:${PATH}"

RUN mkdir -p "${CARGO_HOME}"

ADD sources.list /etc/apt/
ADD config ~/.cargo/

# 安装常用开发工具、Python编译所需依赖与 rust 组件
RUN DEBIAN_FRONTEND=noninteractive apt-get update -y && \
    apt-get install -y git wget bzip2 \
    build-essential libncurses-dev \
    scons libclang-dev libfuse-dev && \
    apt-get clean -y



# 编译并安装 Python 3.13.5
RUN set -eux; \
    PYVER=3.13.5; \
    wget -q https://www.python.org/ftp/python/${PYVER}/Python-${PYVER}.tgz && \
    tar -xzf Python-${PYVER}.tgz && cd Python-${PYVER} && \
    ./configure --enable-optimizations --with-ensurepip=install && \
    make -j"$(nproc)" && make altinstall && cd .. && \
    rm -rf Python-${PYVER} Python-${PYVER}.tgz

# 第二阶段：在 base 基础上准备 c2rust 专用镜像
FROM base AS c2rust

# 软链接 python/pip 指向 3.13 版本，兼容脚本调用 python
RUN if [ -x /usr/local/bin/python3.13 ]; then \
        ln -sf /usr/local/bin/python3.13 /usr/local/bin/python; \
        ln -sf /usr/local/bin/python3.13 /usr/bin/python; \
    fi && \
    if [ -x /usr/local/bin/pip3.13 ]; then \
        ln -sf /usr/local/bin/pip3.13 /usr/local/bin/pip; \
        ln -sf /usr/local/bin/pip3.13 /usr/bin/pip; \
    fi

# 安装 c2rust / 分析所需额外工具
RUN apt-get update -y && \
        apt-get install -y --no-install-recommends \
            graphviz universal-ctags clang-14 libclang-14-dev sudo cloc cmake && \
        apt-get clean && rm -rf /var/lib/apt/lists/*

ENV PATH="/usr/bin:$PATH"
COPY requirements.txt /app/requirements.txt
RUN python -m pip config set global.index-url https://mirrors.aliyun.com/pypi/simple && \
    python -m pip config set global.trusted-host mirrors.aliyun.com
RUN python -m pip install --no-cache-dir pip==25.2 setuptools wheel && \
    python -m pip install --no-cache-dir -r /app/requirements.txt

WORKDIR /root
CMD ["bash"]