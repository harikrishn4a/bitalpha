# Bitcoin Trend Alert — Setup Guide

## Phase 2: Telegram Pairing and Chat ID

1. **Start pairing**
   - In Telegram, message [@bit_alphabot](https://t.me/bit_alphabot) `/start`
   - OpenClaw will show a pairing code (or run `openclaw pairing list telegram`)

2. **Approve pairing**
   ```bash
   openclaw pairing approve telegram <CODE>
   ```

3. **Get chat ID**
   - Message [@userinfobot](https://t.me/userinfobot) in Telegram and note your numeric ID
   - Or check gateway logs / `openclaw pairing list telegram` after pairing

4. **Test send**
   ```bash
   openclaw message send --channel telegram --target YOUR_CHAT_ID --message "OpenClaw BTC Alert ready!"
   ```
   Replace `YOUR_CHAT_ID` with your numeric ID (e.g. `123456789`).

5. **Update SKILL.md** (if needed)
   - Edit `skills/bitcoin-trend-alert/SKILL.md`
   - Replace chat ID in the Send digest section (currently 737798118)
