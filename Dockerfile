FROM ultralytics/ultralytics:latest

RUN pip install --no-cache-dir notebook
RUN pip install jupyterthemes
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

RUN jt -t onedork -f roboto -fs 14

ENV WORKSPACE_DIR /workspace
ENV ULTRALYTICS_DIR /usr/src/ultralytics
# Mount the ultralytics directory to the host as anonymous volume
VOLUME $ULTRALYTICS_DIR
# Set the working directory to the ultralytics directory
WORKDIR $WORKSPACE_DIR

# Create a symbolic link to the ultralytics directory
RUN ln -s ${ULTRALYTICS_DIR} ${WORKSPACE_DIR}/ultralytics

EXPOSE 8888

CMD ["jupyter", "notebook", "--ip='*'", "--port=8888", "--no-browser", "--allow-root"]