"""Add Money (+1w / +$10,000) cheat feature with memory synchronization, UI animations, and sound effects."""

import logging
from typing import Optional
from .base import CheatFeature

logger = logging.getLogger(__name__)


class AddMoneyCheat(CheatFeature):
    """Adds +$10,000 (1w) money with sound effect, UI animation, and multiplayer synchronization on keypress."""

    DEFAULT_ADD_AMOUNT = 10000

    def __init__(self, pm, mono, patcher=None, hotkey: str = "F6", add_amount: int = 10000):
        super().__init__(
            name="Add Money (+1w)",
            description=f"Adds +${add_amount:,} (1w) money with sound effect, UI animation, and multiplayer synchronization.",
            hotkey=hotkey,
            pm=pm,
            mono=mono,
            patcher=patcher,
        )
        self.add_amount = add_amount
        self.total_added = 0
        self.last_action_message = ""

        # Cached Mono class and method pointers
        self.mm_class: Optional[int] = None
        self.player_class: Optional[int] = None
        self.player_ui_class: Optional[int] = None

        self.set_money_native: Optional[int] = None
        self.money_sound_native: Optional[int] = None

        # Cached static and field offsets
        self.static_data_addr: Optional[int] = None
        self.money_offset: Optional[int] = None
        self.instance_offset: Optional[int] = None
        self.syncvar_offset: Optional[int] = None

        self.local_player_ptr_addr: Optional[int] = None

    def prepare(self) -> bool:
        """Finds MoneyManager, Player, and PlayerUI classes, resolves offsets, and pre-compiles JIT methods."""
        try:
            self.mm_class = self.mono.find_class("Assembly-CSharp", "MoneyManager")
            self.player_class = self.mono.find_class("Assembly-CSharp", "Player")
            self.player_ui_class = self.mono.find_class("Assembly-CSharp", "PlayerUI")

            # 1. Resolve MoneyManager static data base address & field offsets
            vtable = self.mono.executor.call(
                self.mono.get_export("mono_class_vtable"), self.mono.root_domain, self.mm_class
            )
            self.static_data_addr = self.mono.executor.call(
                self.mono.get_export("mono_vtable_get_static_field_data"), vtable
            )
            self.money_offset = self.mono.get_field_offset(self.mm_class, "<Money>k__BackingField")
            self.instance_offset = self.mono.get_field_offset(self.mm_class, "Instance")
            self.syncvar_offset = self.mono.get_field_offset(self.mm_class, "_money")

            # 2. Resolve Player.LocalPlayer static address
            p_vtable = self.mono.executor.call(
                self.mono.get_export("mono_class_vtable"), self.mono.root_domain, self.player_class
            )
            p_static = self.mono.executor.call(
                self.mono.get_export("mono_vtable_get_static_field_data"), p_vtable
            )
            lp_offset = self.mono.get_field_offset(self.player_class, "LocalPlayer")
            self.local_player_ptr_addr = p_static + lp_offset

            # 3. JIT compile PlayerUI.SetMoney and MoneyManager.MoneySound
            try:
                set_money_m = self.mono.find_method(self.player_ui_class, "SetMoney", 3)
                self.set_money_native = self.mono.compile_method(set_money_m)
            except Exception as e:
                logger.debug(f"Could not compile PlayerUI.SetMoney: {e}")

            try:
                sound_m = self.mono.find_method(self.mm_class, "MoneySound", 2)
                self.money_sound_native = self.mono.compile_method(sound_m)
            except Exception as e:
                logger.debug(f"Could not compile MoneyManager.MoneySound: {e}")

            return self.static_data_addr is not None and self.money_offset is not None
        except Exception as e:
            logger.error(f"Failed to prepare Add Money cheat: {e}")
            return False

    def get_current_balance(self) -> int:
        """Reads current money from in-game static field."""
        if not self.pm or not self.static_data_addr or self.money_offset is None:
            return 0
        try:
            val = self.pm.read_int(self.static_data_addr + self.money_offset)
            return val if isinstance(val, int) else 0
        except Exception:
            return 0

    def add_money(self, amount: Optional[int] = None) -> int:
        """Adds money to the player's balance and triggers all in-game effects.

        WHY WE USE THIS DUAL-LAYER APPROACH INSTEAD OF JUST CALLING MoneyManager.AddMoney():
        -----------------------------------------------------------------------------------
        The game contains a native function: `MoneyManager.AddMoney(int amount, Player player)`
        (which is also called internally by `SellBox.SellItem` when selling fish).

        However, calling `MoneyManager.AddMoney()` directly has two critical limitations:
        1. Multiplayer Client Authority Trap:
           `MoneyManager.AddMoney` begins with `if ((bool)Instance && Instance.IsServerInitialized)`.
           When playing as a joined client in someone else's multiplayer lobby, `IsServerInitialized`
           is FALSE. Therefore, calling `AddMoney()` is silently ignored and adds 0 money.
        2. Host/Singleplayer UI Desync & FishNet Loopback:
           On host/singleplayer, `AddMoney` only updates `_money.Value` (a FishNet SyncVar).
           The game's UI and static balance are updated in `OnChangeMoney(int prev, int next, bool asServer)`,
           which specifically guards with `if (!asServer) { PlayerUI.SetMoney(...); Money = next; }`.
           Because `asServer` is TRUE on the host server, `MoneyManager.Money` (<Money>k__BackingField)
           and the HUD UI do NOT update synchronously until network tick loopback completes.

        OUR SOLUTION:
        - Layer 1 (Authoritative Memory): Directly write `<Money>k__BackingField` and `SyncVar<int>`
          (offsets 0x6C/0x70) so that shop affordability checks (`MoneyManager.CanAfford`) pass 100%
          reliably across Singleplayer, Host, AND Client modes.
        - Layer 2 (Native UI & Audio): Directly invoke `PlayerUI.SetMoney` and `MoneyManager.MoneySound`
          to guarantee the exact same green floating `+$10000` text animation and cash register audio
          without any network latency or desync.
        """
        if amount is None:
            amount = self.add_amount

        if not self.pm or not self.static_data_addr or self.money_offset is None:
            if not self.prepare():
                return 0

        try:
            # 1. Read current money and compute clamped new balance (prevent 32-bit int overflow)
            cur_money = self.pm.read_int(self.static_data_addr + self.money_offset)
            new_money = min(cur_money + amount, 2_000_000_000)

            # 2. Write authoritative static property <Money>k__BackingField (used by CanAfford / Purchasable)
            self.pm.write_int(self.static_data_addr + self.money_offset, new_money)

            # 3. Update SyncVar<int> _money._value on MoneyManager.Instance if present (used by FishNet replication)
            inst_ptr = 0
            if self.instance_offset is not None:
                try:
                    inst_ptr = self.pm.read_ulonglong(self.static_data_addr + self.instance_offset)
                    if inst_ptr and self.syncvar_offset is not None:
                        syncvar_ptr = self.pm.read_ulonglong(inst_ptr + self.syncvar_offset)
                        if syncvar_ptr:
                            # Update SyncVar<int> _value (internal field offsets 0x6C and 0x70)
                            self.pm.write_int(syncvar_ptr + 0x6C, new_money)
                            self.pm.write_int(syncvar_ptr + 0x70, new_money)
                except Exception:
                    pass

            # 4. Trigger native UI animation (PlayerUI.SetMoney: floating +$10000 text & HUD count-up)
            if self.set_money_native:
                try:
                    # PlayerUI.SetMoney(int to, int diff, bool gainedMoney)
                    # RCX = new_money, RDX = amount, R8 = 1 (True)
                    self.mono.executor.call(self.set_money_native, new_money, amount, 1)
                except Exception:
                    pass

            # 5. Play native in-game sound effect (MoneyManager.MoneySound: sell/cash audio clip)
            lp_ptr = 0
            if self.local_player_ptr_addr:
                try:
                    lp_ptr = self.pm.read_ulonglong(self.local_player_ptr_addr)
                except Exception:
                    pass

            if self.money_sound_native and inst_ptr and lp_ptr:
                try:
                    # MoneySound(this, increase, player)
                    # RCX = inst_ptr, RDX = 1 (True), R8 = lp_ptr
                    self.mono.executor.call(self.money_sound_native, inst_ptr, 1, lp_ptr)
                except Exception:
                    pass

            self.total_added += amount
            self.is_enabled = True
            self.last_action_message = f"Added +${amount:,} (+1w) | New Balance: ${new_money:,}"
            return new_money
        except Exception as e:
            logger.error(f"Error adding money: {e}")
            return 0

    def enable(self) -> bool:
        """Executes the add money action."""
        self.add_money()
        return True

    def disable(self) -> bool:
        """No-op for instant action cheat."""
        return True

    def toggle(self) -> bool:
        """Executes the add money action on keypress."""
        self.add_money()
        return True

    def get_status_badge(self) -> str:
        """Returns rich formatted status badge showing current balance."""
        balance = self.get_current_balance()
        if balance > 0:
            return f"[bold green]${balance:,}[/bold green]"
        return "[bold cyan]PRESS TO +1w[/bold cyan]"
