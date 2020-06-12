#!/bin/sh

set -e

ami_config="${CODEBUILD_SRC_DIR}/.ebextensions/00_ami.config"
tmp_file_path="${CODEBUILD_SRC_DIR}/00_ami.interpolated.config"

if [ "$(git rev-parse --abbrev-ref HEAD)" = "release" ]; then
  sed -e "s/\${SECURITY_GROUP_AUTO_SCALING}/sg-0a8bb4762304beedc/" \
      -e "s/\${SECURITY_GROUP_LOAD_BALANCER}/sg-0048170b7468fc90b/" \
      "${ami_config}" > "${tmp_file_path}"
else
  sed -e "s/\${SECURITY_GROUP_AUTO_SCALING}/sg-0a8a13d817cb48f85/" \
      -e "s/\${SECURITY_GROUP_LOAD_BALANCER}/sg-0563c2648b0b301eb/" \
      "${ami_config}" > "${tmp_file_path}"
fi

mv "${tmp_file_path}" "${ami_config}"

exit
