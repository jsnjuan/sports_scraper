# ==========================
# BROWSER
# ==========================

HEADLESS = False

# ==========================
# PAGINATION
# ==========================

PER_PAGE = 20

# ==========================
# CONTEXT CONTROL
# ==========================

CONTEXT_RESTART_INTERVAL = 100  # Restart the context every N pages

# ==========================
# RETRIES
# ==========================

MAX_RETRIES_PER_PAGE = 5
TOKEN_RETRY_DELAY = 5
SOFT_BLOCK_DELAY = 20

# ==========================
# DELAY
# ==========================

DELAY_BASE = 60
DELAY_JITTER = 10

DELAY_PAGE = 60
DELAY_CATEGORY = 300
DELAY_EVENT = 1800
