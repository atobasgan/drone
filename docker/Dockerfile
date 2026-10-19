# Ubuntu 26.04 + ROS 2 Lyrical + Gazebo (Jetty, ros_gz ile) + PX4 SITL bagimliliklari
# + Micro XRCE-DDS Agent + llama.cpp. Kurulumu tekrarlanabilir yapar (Gorev 0.7).
#
#   docker compose -f docker/docker-compose.yml build
#   docker compose -f docker/docker-compose.yml run --rm dev
#
# Not: Lyrical/Jetty yeni surumler; resmi ros imaj etiketi farkliysa ROS_IMAGE'i
# degistir. PX4 bu Gazebo ile derlenmezse B plani: ROS_IMAGE ve ROS_DISTRO'yu
# PX4'un resmi destekledigi ikiliye cevir (ornek: ros:jazzy + Gazebo Harmonic);
# projenin geri kalani degismez.
ARG ROS_IMAGE=ros:lyrical-ros-base
FROM ${ROS_IMAGE}

ARG ROS_DISTRO=lyrical
ARG PX4_VERSION=main
ENV DEBIAN_FRONTEND=noninteractive \
    ROS_DISTRO=${ROS_DISTRO} \
    PX4_DIR=/opt/PX4-Autopilot \
    XRCE_AGENT_DIR=/opt/Micro-XRCE-DDS-Agent \
    LLAMA_CPP_DIR=/opt/llama.cpp \
    LLM_DRONE_DIR=/workspace/llm_drone

RUN apt-get update && apt-get install -y --no-install-recommends \
      git curl wget sudo tmux build-essential cmake ninja-build \
      python3-pip python3-pytest python3-requests python3-yaml \
      libcurl4-openssl-dev \
      ros-${ROS_DISTRO}-desktop ros-${ROS_DISTRO}-ros-gz ros-dev-tools \
    && rm -rf /var/lib/apt/lists/*

# PX4 SITL (bagimliliklar + bir kez derleme, sonraki acilislar hizli)
RUN git clone --recursive -b ${PX4_VERSION} https://github.com/PX4/PX4-Autopilot.git ${PX4_DIR} \
    && bash ${PX4_DIR}/Tools/setup/ubuntu.sh --no-nuttx \
    && cd ${PX4_DIR} && make px4_sitl \
    && rm -rf /var/lib/apt/lists/*

# Micro XRCE-DDS Agent
RUN git clone https://github.com/eProsima/Micro-XRCE-DDS-Agent.git ${XRCE_AGENT_DIR} \
    && cmake -S ${XRCE_AGENT_DIR} -B ${XRCE_AGENT_DIR}/build \
    && cmake --build ${XRCE_AGENT_DIR}/build -j"$(nproc)" \
    && cmake --install ${XRCE_AGENT_DIR}/build && ldconfig /usr/local/lib/

# llama.cpp (CPU). GPU icin: --build-arg LLAMA_CMAKE_ARGS="-DGGML_CUDA=ON" ve CUDA'li taban imaj.
ARG LLAMA_CMAKE_ARGS=""
RUN git clone https://github.com/ggml-org/llama.cpp.git ${LLAMA_CPP_DIR} \
    && cmake -S ${LLAMA_CPP_DIR} -B ${LLAMA_CPP_DIR}/build ${LLAMA_CMAKE_ARGS} \
    && cmake --build ${LLAMA_CPP_DIR}/build --config Release -j"$(nproc)" --target llama-server

RUN echo "source /opt/ros/${ROS_DISTRO}/setup.bash" >> /root/.bashrc \
    && echo '[ -f ${LLM_DRONE_DIR}/ros2_ws/install/setup.bash ] && source ${LLM_DRONE_DIR}/ros2_ws/install/setup.bash' >> /root/.bashrc

WORKDIR ${LLM_DRONE_DIR}
CMD ["bash"]
