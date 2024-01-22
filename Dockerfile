FROM ultralytics/ultralytics:latest

# Install jupyterlab
RUN pip install --no-cache-dir jupyterlab jupyterthemes
# Install jupyterlab extensions
RUN pip install --no-cache-dir jupyter-ai-chatgpt jupyterlab-git jupyterlab-github
# NOTE: https://github.com/dunovank/jupyter-themes
# -fs 115: Code font size
# -nfs 125: Notebook menu font size
# -tfs 115: Markdown font size
# -dfs 115 : pandas DataFrame font size
# -ofs 115: Output area font size
# -cursc r: cursor color red (red seems to be the most noticeable in onedork theme)
# -cellw 80%: Cell width 80% (the larger the number, the fuller the screen)
# -lineh 115 : code line spacing
# -altmd: Option to make the background of Markdown cells transparent.
# -kl: Display the kernel logo (python logo in the upper right corner of the laptop screen)
# -T: Display toolbar under menu tab (save, add/delete/move cell, stop/restart kernel, etc.)
# -N: Display file name on laptop screen

RUN jt -t onedork -f firacode -nf robotosans -fs 14 -nfs 14

ENV WORKSPACE_DIR /workspace
ENV PROJECT_DIR ${WORKSPACE_DIR}/project
ENV ULTRALYTICS_DIR /usr/src/ultralytics
# Mount the ultralytics directory to the host as anonymous volume
VOLUME $ULTRALYTICS_DIR
# Set the working directory to the ultralytics directory
WORKDIR $PROJECT_DIR

# Create a symbolic link to the ultralytics directory
RUN ln -s ${ULTRALYTICS_DIR} ${WORKSPACE_DIR}/ultralytics-src

# Expose jupyter port
EXPOSE 8888
# Expose tensorboard port
EXPOSE 6006

ENTRYPOINT [ "jupyter", "lab", "--allow-root", "--no-browser", "--NotebookApp.allow_origin='*'", "--NotebookApp.allow_remote_access=True", "--NotebookApp.ip='*'" ]
CMD [ "" ]