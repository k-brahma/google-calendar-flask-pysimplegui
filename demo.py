#!/usr/bin/env python
"""
Google Calendar CRUD デモスクリプト
"""

from gcal.calendar_crud_demo import demonstrate_crud_operations

if __name__ == "__main__":
    # Google Meetを使わずにデモを実行
    demonstrate_crud_operations(create_meet=False)
