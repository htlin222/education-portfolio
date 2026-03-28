.PHONY: setup list parse

USER ?=

ifdef USER
  USER_FLAG = -u $(USER)
else
  USER_FLAG =
endif

setup:
	uv sync

list:
	uv run python -m evalbot $(USER_FLAG) list

parse:
	uv run python -m evalbot $(USER_FLAG) parse --sfid=$(SFID)

# Usage:
#   make list                    # default profile
#   make list USER=user1         # specific user
#   make parse SFID=88492 USER=user1
