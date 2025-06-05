FROM fedora:39
LABEL Name=lab0
LABEL Version=1

# в метаданные образа пару ключ=значение
ARG STUDENT=test
ENV STUDENT=$STUDENT

# выполняется только в момент docker build (при сборке образа) (т.е. 1 раз).
# В результате устанавливаются пакеты и создаётся слой с уже готовой системой.
# \ это «объедини эту строку со следующей».
# dnf install — команда менеджера пакетов Fedora (DNF), для установки пакетов.
# Оператор && выполняет следующую команду только если предыдущая завершилась успешно
RUN dnf install --nodocs --setopt=install_weak_deps=False -y \
    sudo \
    util-linux \
    git \
    curl \
    vim \
    nano \
    python3-requests \
    && rm -rf /var/cache /var/log/dnf* /var/log/yum.* \
    && dnf clean all

# в отдельный RUN, потому что здесь решается другая задача — не установка пакетов, а создание системных сущностей (группы и пользователя).
RUN groupadd -g 1000 $STUDENT \
    && useradd -ms /bin/bash -u 1000 -g $STUDENT $STUDENT


RUN echo "$STUDENT:$STUDENT" | chpasswd \
    && echo "$STUDENT ALL=(ALL) NOPASSWD:ALL" | sudo tee /etc/sudoers.d/$STUDENT

RUN echo "alias ll='ls -alF'" | su $STUDENT -c "tee -a /home/$STUDENT/.bashrc"
RUN echo "alias la='ls -A'" | su $STUDENT -c "tee -a /home/$STUDENT/.bashrc"
RUN echo "alias l='ls -CF'" | su $STUDENT -c "tee -a /home/$STUDENT/.bashrc"

USER $STUDENT

ENTRYPOINT [ "/bin/bash" ]