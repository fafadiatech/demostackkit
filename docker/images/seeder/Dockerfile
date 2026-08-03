# demostackkit seeder image
# Based on ERPNext v15 so seeder scripts can import frappe directly.
# demostackkit is installed on top for the CLI and seeder framework.

FROM frappe/erpnext:v15

USER root

# Install Python build tools (may already be present)
RUN apt-get update -qq && \
    apt-get install -y --no-install-recommends \
        python3-pip \
        curl \
    && rm -rf /var/lib/apt/lists/*

# Copy and install demostackkit
WORKDIR /demostackkit
COPY . /demostackkit/
RUN pip install --no-cache-dir -e /demostackkit

# The industries/ directory is mounted at runtime:
# -v ./industries:/demostackkit/industries:ro

COPY docker/images/seeder/entrypoint.sh /entrypoint.sh
RUN chmod +x /entrypoint.sh

USER frappe
WORKDIR /home/frappe/frappe-bench

ENTRYPOINT ["/entrypoint.sh"]
