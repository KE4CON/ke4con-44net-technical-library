/**
 * FieldComms — Operator Identity  (identity.js  v3)
 *
 * Handles ALL person types that appear in MCESV/MCEMA activations:
 *
 *   TYPE 1 — ESV Member, Ham
 *     Has: member_id (ESV-###) + callsign + radio_id (Starcom)
 *     Shown as: callsign  |  ESV-042 · 1042
 *
 *   TYPE 2 — ESV Member, Non-Ham
 *     Has: member_id (ESV-###) + radio_id (Starcom), NO callsign
 *     Shown as: member_id  |  ESV-042 · 1042
 *
 *   TYPE 3 — Mutual Aid / Visitor, Ham
 *     Has: callsign + their agency, NO ESV member_id
 *     Auto-assigned VIS-##### on promote-to-roster
 *     Shown as: callsign  |  VISITOR · Lake County ARES
 *
 *   TYPE 4 — Mutual Aid / Visitor, Non-Ham
 *     Has: name + radio_id + their agency, NO callsign, NO ESV member_id
 *     Shown as: radio_id  |  VISITOR · Red Cross
 *
 * Identity stored in localStorage:
 *   {
 *     member_id      : "ESV-042",   // ESV number, or "VIS-#####" for visitors
 *     callsign       : "K9ESV",     // blank if non-ham
 *     radio_id       : "1042",      // Starcom radio ID (all ESV members have one)
 *     first_name     : "Jim",
 *     last_name      : "Anderson",
 *     name           : "Jim Anderson",
 *     role           : "Operator",
 *     member_type    : "member" | "visitor" | "mutual_aid",
 *     visitor_agency : "",           // agency name for visitors
 *     is_ham         : true | false,
 *   }
 *
 * Public API:
 *   FC_ID.getMemberId()    → "ESV-042"
 *   FC_ID.getCallsign()    → "K9ESV" or ""
 *   FC_ID.getRadioId()     → "1042" or ""
 *   FC_ID.getDisplayId()   → best single identifier for logging
 *   FC_ID.getName()        → "Jim Anderson"
 *   FC_ID.getRole()        → "Operator"
 *   FC_ID.getMemberType()  → "member" | "visitor" | "mutual_aid"
 *   FC_ID.isHam()          → true | false
 *   FC_ID.isVisitor()      → true | false
 *   FC_ID.getIdentity()    → full object copy
 *   FC_ID.showPicker()     → open the picker modal
 *   FC_ID.onSet(fn)        → callback when identity confirmed
 *   FC_ID.clear()          → forget + reopen picker
 */
const FC_ID = (() => {
    const STORE_KEY = 'fc_operator_identity_v3';
    const API       = 'http://localhost:5050';

    let _id     = null;
    let _roster = [];
    let _picker = null;
    let _cbs    = [];

    // ── Helpers ───────────────────────────────────────────────────────────────
    function esc(s) {
        return String(s||'').replace(/&/g,'&amp;').replace(/</g,'&lt;').replace(/>/g,'&gt;');
    }

    /**
     * Best single identifier for a person object (roster row or identity).
     * Priority: callsign → radio_id → member_id → name
     */
    function bestId(m) {
        return (m.callsign || m.radio_id || m.member_id || m.name || '').trim();
    }

    // ── Persistence ───────────────────────────────────────────────────────────
    function load() {
        try {
            const s = localStorage.getItem(STORE_KEY);
            if (s) _id = JSON.parse(s);
        } catch(e) {}
        return _id;
    }

    function save(id) {
        _id = id;
        try { localStorage.setItem(STORE_KEY, JSON.stringify(id)); } catch(e) {}
        _cbs.forEach(fn => { try { fn({ ..._id }); } catch(e) {} });
        renderBadge();
    }

    // ── Roster fetch ──────────────────────────────────────────────────────────
    async function fetchRoster() {
        try {
            const r = await fetch(`${API}/api/roster/members`,
                                  { signal: AbortSignal.timeout(3000) });
            if (r.ok) {
                const all = await r.json();
                // Only ESV members in the roster picker — visitors get added manually
                _roster = all
                    .filter(m => !m.is_visitor && m.member_type !== 'visitor'
                                              && m.member_type !== 'mutual_aid')
                    .sort((a, b) =>
                        (a.last_name||'').localeCompare(b.last_name||''));
            }
        } catch(e) { /* offline — picker works with manual entry */ }
    }

    // ── Picker ────────────────────────────────────────────────────────────────
    function buildPicker() {
        closePicker();

        const ov = document.createElement('div');
        ov.id = 'fc-id-overlay';
        ov.style.cssText =
            'position:fixed;inset:0;background:rgba(0,0,0,0.6);z-index:9000;' +
            'display:flex;align-items:center;justify-content:center;padding:16px;' +
            'font-family:"Share Tech Mono","Courier New",monospace;';

        ov.innerHTML = `
<div style="
    background:#fff;border-radius:12px;width:min(480px,100%);
    box-shadow:0 8px 40px rgba(0,0,0,0.3);overflow:hidden;">

  <!-- ── Header ── -->
  <div style="background:#1a3a6b;padding:16px 20px 12px;border-bottom:3px solid #f0c040">
    <div style="display:flex;align-items:center;gap:12px">
      <div style="font-size:28px;line-height:1">🪪</div>
      <div>
        <div style="font-family:'Oswald','Arial Narrow',sans-serif;
             font-size:17px;color:#fff;letter-spacing:2px">IDENTIFY YOURSELF</div>
        <div style="font-size:10px;color:rgba(255,255,255,0.55);margin-top:2px">
          McHenry County Emergency Services Volunteers and McHenry County Emergency Management Agency · K9ESV
        </div>
      </div>
    </div>
  </div>

  <!-- ── Body ── -->
  <div style="padding:18px 20px 14px">

    <!-- Who are you? -->
    <div style="display:flex;gap:0;margin-bottom:14px;
                border:1.5px solid #b0c4dc;border-radius:7px;overflow:hidden">
      <button data-who="member" style="
          flex:1;padding:9px 4px;border:none;cursor:pointer;font-size:11px;
          background:#1a3a6b;color:#fff;font-family:inherit;letter-spacing:0.05em;
          border-right:1px solid #b0c4dc;">
        🪪 ESV MEMBER
      </button>
      <button data-who="visitor" style="
          flex:1;padding:9px 4px;border:none;cursor:pointer;font-size:11px;
          background:#eef2f7;color:#4a6080;font-family:inherit;letter-spacing:0.05em;">
        🤝 VISITOR / MUTUAL AID
      </button>
    </div>

    <!-- ═══ ESV MEMBER PANEL ═══ -->
    <div id="fc-panel-member">

      <div style="font-size:10px;color:#4a6080;letter-spacing:0.1em;
                  text-transform:uppercase;margin-bottom:5px;font-weight:bold">
        Select from ESV Roster
      </div>
      <select id="fc-id-sel" style="
          width:100%;padding:10px 8px;font-size:13px;border-radius:6px;
          border:1.5px solid #b0c4dc;background:#f4f6f9;color:#0f1e38;
          cursor:pointer;font-family:inherit;box-sizing:border-box;margin-bottom:12px;">
        <option value="">— Choose your name —</option>
      </select>

      <!-- divider -->
      <div style="display:flex;align-items:center;gap:10px;margin-bottom:12px">
        <div style="flex:1;height:1px;background:#dce6f0"></div>
        <div style="font-size:10px;color:#8090a8">OR ENTER MANUALLY</div>
        <div style="flex:1;height:1px;background:#dce6f0"></div>
      </div>

      <!-- 3-column grid: Member ID | Callsign | Starcom ID -->
      <div style="display:grid;grid-template-columns:1fr 1fr 1fr;gap:8px;margin-bottom:10px">
        <div>
          <div style="font-size:9.5px;color:#4a6080;margin-bottom:3px;letter-spacing:0.06em;text-transform:uppercase">
            ESV Member ID
          </div>
          <input id="fc-mid" type="text" placeholder="ESV-042"
            style="width:100%;box-sizing:border-box;padding:8px;font-size:12px;
                   border-radius:5px;border:1.5px solid #b0c4dc;background:#f4f6f9;
                   font-family:inherit;color:#0f1e38;text-transform:uppercase;">
        </div>
        <div>
          <div style="font-size:9.5px;color:#4a6080;margin-bottom:3px;letter-spacing:0.06em;text-transform:uppercase">
            Callsign <span style="color:#9090a8;font-size:8px">(hams only)</span>
          </div>
          <input id="fc-call" type="text" placeholder="K9ESV"
            style="width:100%;box-sizing:border-box;padding:8px;font-size:12px;
                   border-radius:5px;border:1.5px solid #b0c4dc;background:#f4f6f9;
                   font-family:inherit;color:#1a3a6b;text-transform:uppercase;letter-spacing:1px;">
        </div>
        <div>
          <div style="font-size:9.5px;color:#4a6080;margin-bottom:3px;letter-spacing:0.06em;text-transform:uppercase">
            Starcom Radio ID
          </div>
          <input id="fc-rid" type="text" placeholder="1042"
            style="width:100%;box-sizing:border-box;padding:8px;font-size:12px;
                   border-radius:5px;border:1.5px solid #b0c4dc;background:#f4f6f9;
                   font-family:inherit;color:#0f1e38;">
        </div>
      </div>

      <div style="display:grid;grid-template-columns:1fr 1fr;gap:8px;margin-bottom:14px">
        <div>
          <div style="font-size:9.5px;color:#4a6080;margin-bottom:3px;letter-spacing:0.06em;text-transform:uppercase">First Name</div>
          <input id="fc-fname" type="text" placeholder="First name"
            style="width:100%;box-sizing:border-box;padding:8px;font-size:12px;
                   border-radius:5px;border:1.5px solid #b0c4dc;background:#f4f6f9;
                   font-family:inherit;color:#0f1e38;">
        </div>
        <div>
          <div style="font-size:9.5px;color:#4a6080;margin-bottom:3px;letter-spacing:0.06em;text-transform:uppercase">Last Name</div>
          <input id="fc-lname" type="text" placeholder="Last name"
            style="width:100%;box-sizing:border-box;padding:8px;font-size:12px;
                   border-radius:5px;border:1.5px solid #b0c4dc;background:#f4f6f9;
                   font-family:inherit;color:#0f1e38;">
        </div>
      </div>
    </div>

    <!-- ═══ VISITOR / MUTUAL AID PANEL ═══ -->
    <div id="fc-panel-visitor" style="display:none">

      <div style="background:#fef3d8;border:1px solid #e6b054;border-radius:6px;
                  padding:10px 12px;margin-bottom:12px;font-size:11px;color:#7a4a00;line-height:1.5">
        <strong>⚠ Visitor / Mutual Aid</strong><br>
        You are not an ESV member. You'll be logged as a visitor.
        Net Control can promote you to the roster after check-in.
      </div>

      <div style="display:grid;grid-template-columns:1fr 1fr;gap:8px;margin-bottom:8px">
        <div>
          <div style="font-size:9.5px;color:#4a6080;margin-bottom:3px;letter-spacing:0.06em;text-transform:uppercase">First Name *</div>
          <input id="fc-vis-fname" type="text" placeholder="First name"
            style="width:100%;box-sizing:border-box;padding:8px;font-size:12px;
                   border-radius:5px;border:1.5px solid #b0c4dc;background:#f4f6f9;
                   font-family:inherit;color:#0f1e38;">
        </div>
        <div>
          <div style="font-size:9.5px;color:#4a6080;margin-bottom:3px;letter-spacing:0.06em;text-transform:uppercase">Last Name *</div>
          <input id="fc-vis-lname" type="text" placeholder="Last name"
            style="width:100%;box-sizing:border-box;padding:8px;font-size:12px;
                   border-radius:5px;border:1.5px solid #b0c4dc;background:#f4f6f9;
                   font-family:inherit;color:#0f1e38;">
        </div>
      </div>

      <div style="display:grid;grid-template-columns:1fr 1fr;gap:8px;margin-bottom:8px">
        <div>
          <div style="font-size:9.5px;color:#4a6080;margin-bottom:3px;letter-spacing:0.06em;text-transform:uppercase">
            Callsign <span style="color:#9090a8;font-size:8px">(if licensed)</span>
          </div>
          <input id="fc-vis-call" type="text" placeholder="Optional"
            style="width:100%;box-sizing:border-box;padding:8px;font-size:12px;
                   border-radius:5px;border:1.5px solid #b0c4dc;background:#f4f6f9;
                   font-family:inherit;color:#1a3a6b;text-transform:uppercase;letter-spacing:1px;">
        </div>
        <div>
          <div style="font-size:9.5px;color:#4a6080;margin-bottom:3px;letter-spacing:0.06em;text-transform:uppercase">
            Radio ID <span style="color:#9090a8;font-size:8px">(if assigned)</span>
          </div>
          <input id="fc-vis-rid" type="text" placeholder="Optional"
            style="width:100%;box-sizing:border-box;padding:8px;font-size:12px;
                   border-radius:5px;border:1.5px solid #b0c4dc;background:#f4f6f9;
                   font-family:inherit;color:#0f1e38;">
        </div>
      </div>

      <div style="margin-bottom:14px">
        <div style="font-size:9.5px;color:#4a6080;margin-bottom:3px;letter-spacing:0.06em;text-transform:uppercase">
          Your Agency / Organization *
        </div>
        <input id="fc-vis-agency" type="text"
          placeholder="e.g. Lake County ARES, Red Cross, CERT, Woodstock Fire Dept"
          style="width:100%;box-sizing:border-box;padding:8px;font-size:12px;
                 border-radius:5px;border:1.5px solid #b0c4dc;background:#f4f6f9;
                 font-family:inherit;color:#0f1e38;">
      </div>
    </div>

    <!-- Preview -->
    <div id="fc-preview" style="
        display:none;background:#eef2f7;border:1.5px solid #b0c4dc;
        border-radius:8px;padding:10px 14px;margin-bottom:12px;"></div>

    <!-- Error -->
    <div id="fc-err" style="
        display:none;background:#fde8e8;border:1px solid #d08080;border-radius:5px;
        padding:8px 12px;margin-bottom:10px;font-size:12px;color:#b82020;"></div>

    <!-- Buttons -->
    <div style="display:flex;gap:8px">
      <button id="fc-skip" style="
          background:#f0f2f5;border:1px solid #c0ccd8;border-radius:6px;
          padding:10px 14px;font-size:12px;cursor:pointer;color:#4a6080;
          font-family:inherit;">Skip for now</button>
      <button id="fc-ok" style="
          flex:1;background:#1a3a6b;border:none;border-radius:6px;
          padding:10px;font-size:14px;font-weight:bold;cursor:pointer;
          color:#fff;font-family:inherit;letter-spacing:1px;">
        ✓ &nbsp;CONFIRM
      </button>
    </div>
    <div style="font-size:10px;color:#a0aab8;text-align:center;margin-top:8px">
      Saved on this device · No password required · Change anytime
    </div>

  </div>
</div>`;

        document.body.appendChild(ov);
        _picker = ov;

        // ── Roster dropdown population ─────────────────────────────────────────
        const sel = ov.querySelector('#fc-id-sel');
        if (_roster.length > 0) {
            const hams    = _roster.filter(m => m.callsign);
            const nonhams = _roster.filter(m => !m.callsign);
            if (hams.length) {
                const g = document.createElement('optgroup');
                g.label = '📻 Amateur Operators';
                hams.forEach(m => g.appendChild(_makeOpt(m)));
                sel.appendChild(g);
            }
            if (nonhams.length) {
                const g = document.createElement('optgroup');
                g.label = '🪪 ESV Members (non-ham)';
                nonhams.forEach(m => g.appendChild(_makeOpt(m)));
                sel.appendChild(g);
            }
        } else {
            const o = document.createElement('option');
            o.value = ''; o.disabled = true;
            o.text = '(Roster not loaded — enter manually below)';
            sel.appendChild(o);
        }

        // ── Restore previous identity ──────────────────────────────────────────
        if (_id) {
            const isVis = _id.member_type === 'visitor' || _id.member_type === 'mutual_aid';
            if (isVis) {
                _setWho('visitor');
                ov.querySelector('#fc-vis-fname').value  = _id.first_name  || '';
                ov.querySelector('#fc-vis-lname').value  = _id.last_name   || '';
                ov.querySelector('#fc-vis-call').value   = _id.callsign    || '';
                ov.querySelector('#fc-vis-rid').value    = _id.radio_id    || '';
                ov.querySelector('#fc-vis-agency').value = _id.visitor_agency || '';
            } else {
                ov.querySelector('#fc-mid').value   = _id.member_id  || '';
                ov.querySelector('#fc-call').value  = _id.callsign   || '';
                ov.querySelector('#fc-rid').value   = _id.radio_id   || '';
                ov.querySelector('#fc-fname').value = _id.first_name || '';
                ov.querySelector('#fc-lname').value = _id.last_name  || '';
            }
            _updatePreview();
        }

        // ── Who-are-you toggle ─────────────────────────────────────────────────
        ov.querySelectorAll('[data-who]').forEach(btn => {
            btn.addEventListener('click', () => {
                _setWho(btn.dataset.who);
                _updatePreview();
            });
        });

        function _setWho(who) {
            ov.querySelectorAll('[data-who]').forEach(b => {
                const active = b.dataset.who === who;
                b.style.background = active ? '#1a3a6b' : '#eef2f7';
                b.style.color      = active ? '#fff'    : '#4a6080';
            });
            ov.querySelector('#fc-panel-member').style.display  = who === 'member'  ? '' : 'none';
            ov.querySelector('#fc-panel-visitor').style.display = who === 'visitor' ? '' : 'none';
        }
        // expose to outer scope
        _setWhoFn = _setWho;

        // ── Input events → preview ─────────────────────────────────────────────
        const inputs = ov.querySelectorAll('input, select');
        inputs.forEach(el => el.addEventListener('input', _updatePreview));
        inputs.forEach(el => el.addEventListener('change', _updatePreview));

        // Uppercase certain fields
        ov.querySelector('#fc-call').addEventListener('input', e => {
            e.target.value = e.target.value.toUpperCase().replace(/[^A-Z0-9\/]/g,'');
        });
        ov.querySelector('#fc-vis-call').addEventListener('input', e => {
            e.target.value = e.target.value.toUpperCase().replace(/[^A-Z0-9\/]/g,'');
        });
        ov.querySelector('#fc-mid').addEventListener('input', e => {
            e.target.value = e.target.value.toUpperCase().replace(/[^A-Z0-9\-]/g,'');
        });

        // Roster select auto-fills manual fields
        sel.addEventListener('change', () => {
            if (!sel.value) return;
            const m = JSON.parse(sel.value);
            ov.querySelector('#fc-mid').value   = m.member_id  || '';
            ov.querySelector('#fc-call').value  = m.callsign   || '';
            ov.querySelector('#fc-rid').value   = m.radio_id   || '';
            ov.querySelector('#fc-fname').value = m.first_name || '';
            ov.querySelector('#fc-lname').value = m.last_name  || '';
            _updatePreview();
        });

        function _updatePreview() {
            const isVis = ov.querySelector('[data-who="visitor"]')
                             .style.background === 'rgb(26, 58, 107)';
            let m;
            if (isVis) {
                m = {
                    first_name:     ov.querySelector('#fc-vis-fname').value.trim(),
                    last_name:      ov.querySelector('#fc-vis-lname').value.trim(),
                    callsign:       ov.querySelector('#fc-vis-call').value.trim(),
                    radio_id:       ov.querySelector('#fc-vis-rid').value.trim(),
                    visitor_agency: ov.querySelector('#fc-vis-agency').value.trim(),
                    member_type:    'visitor',
                };
            } else {
                m = {
                    member_id:  ov.querySelector('#fc-mid').value.trim(),
                    callsign:   ov.querySelector('#fc-call').value.trim(),
                    radio_id:   ov.querySelector('#fc-rid').value.trim(),
                    first_name: ov.querySelector('#fc-fname').value.trim(),
                    last_name:  ov.querySelector('#fc-lname').value.trim(),
                    member_type: 'member',
                };
            }
            const hasData = Object.values(m).some(v => v);
            const prev = ov.querySelector('#fc-preview');
            if (!hasData) { prev.style.display = 'none'; return; }
            prev.style.display = 'block';
            prev.innerHTML = _previewHtml(m);
        }

        // ── Confirm ────────────────────────────────────────────────────────────
        ov.querySelector('#fc-ok').addEventListener('click', () => {
            ov.querySelector('#fc-err').style.display = 'none';
            const isVis = ov.querySelector('[data-who="visitor"]')
                             .style.background === 'rgb(26, 58, 107)';
            let id;

            if (isVis) {
                const fn     = ov.querySelector('#fc-vis-fname').value.trim();
                const ln     = ov.querySelector('#fc-vis-lname').value.trim();
                const cs     = ov.querySelector('#fc-vis-call').value.trim();
                const rid    = ov.querySelector('#fc-vis-rid').value.trim();
                const agency = ov.querySelector('#fc-vis-agency').value.trim();
                const name   = [fn, ln].filter(Boolean).join(' ');
                if (!name) {
                    _showErr('Please enter your first and last name.'); return;
                }
                if (!agency) {
                    _showErr('Please enter your agency or organization.'); return;
                }
                id = {
                    member_id:      '',          // no ESV number
                    callsign:       cs,
                    radio_id:       rid,
                    first_name:     fn,
                    last_name:      ln,
                    name,
                    role:           'Visitor',
                    member_type:    'visitor',
                    visitor_agency: agency,
                    is_ham:         !!cs,
                };
            } else {
                const mid  = ov.querySelector('#fc-mid').value.trim();
                const cs   = ov.querySelector('#fc-call').value.trim();
                const rid  = ov.querySelector('#fc-rid').value.trim();
                const fn   = ov.querySelector('#fc-fname').value.trim();
                const ln   = ov.querySelector('#fc-lname').value.trim();
                const name = [fn, ln].filter(Boolean).join(' ');
                if (!mid && !cs && !rid) {
                    _showErr('Please enter your Member ID, Callsign, or Starcom Radio ID.'); return;
                }
                id = {
                    member_id:      mid,
                    callsign:       cs,
                    radio_id:       rid,
                    first_name:     fn,
                    last_name:      ln,
                    name:           name || cs || mid || rid,
                    role:           'Operator',
                    member_type:    'member',
                    visitor_agency: '',
                    is_ham:         !!cs,
                };
                // Pull role from roster if selected
                if (sel.value) {
                    try { id.role = JSON.parse(sel.value).role || 'Operator'; }
                    catch(e) {}
                }
            }
            save(id);
            closePicker();
        });

        function _showErr(msg) {
            const el = ov.querySelector('#fc-err');
            el.textContent = msg;
            el.style.display = 'block';
        }

        ov.querySelector('#fc-skip').addEventListener('click', closePicker);
        setTimeout(() => ov.querySelector('#fc-id-sel').focus(), 80);
    }

    // ── Make roster option ────────────────────────────────────────────────────
    function _makeOpt(m) {
        const opt  = document.createElement('option');
        opt.value  = JSON.stringify(m);
        const name = [m.first_name, m.last_name].filter(Boolean).join(' ');
        const id   = m.callsign || m.radio_id || m.member_id || '?';
        // Pad to align names: ID left, name right
        opt.text   = `${id.padEnd(9)}  ${name}  ${m.radio_id && !m.callsign ? '·'+m.radio_id : ''}`;
        return opt;
    }

    // ── Preview block HTML ────────────────────────────────────────────────────
    function _previewHtml(m) {
        const isVis = m.member_type === 'visitor' || m.member_type === 'mutual_aid';
        const name  = m.name || [m.first_name, m.last_name].filter(Boolean).join(' ') || '—';
        const icon  = m.callsign ? '📻' : (isVis ? '🤝' : '🪪');
        const disp  = m.callsign || m.radio_id || m.member_id || name;
        const sub   = [
            m.member_id ? `ESV-ID: ${m.member_id}` : null,
            m.radio_id  ? `Radio: ${m.radio_id}`  : null,
            isVis && m.visitor_agency ? m.visitor_agency : null,
        ].filter(Boolean).join(' · ');

        return `<div style="display:flex;align-items:center;gap:12px">
            <div style="font-size:26px">${icon}</div>
            <div>
              <div style="font-family:'Oswald','Arial Narrow',sans-serif;
                   font-size:17px;color:#1a3a6b;letter-spacing:1px">${esc(disp)}</div>
              <div style="font-size:11px;color:#0f1e38;margin-top:1px">${esc(name)}</div>
              ${sub ? `<div style="font-size:10px;color:#4a6080;margin-top:2px">${esc(sub)}</div>` : ''}
              ${isVis ? '<div style="font-size:10px;color:#c8760a;margin-top:2px">⚠ VISITOR — will be logged as guest</div>' : ''}
            </div></div>`;
    }

    function closePicker() {
        if (_picker) { document.body.removeChild(_picker); _picker = null; }
    }

    // ── Header badge ──────────────────────────────────────────────────────────
    function renderBadge() {
        const el = document.getElementById('fc-operator-badge');
        if (!el) return;

        if (_id && (_id.name || _id.callsign || _id.member_id || _id.radio_id)) {
            const disp   = _id.callsign || _id.radio_id || _id.member_id || '';
            const icon   = _id.member_type === 'visitor' ? '🤝'
                         : _id.is_ham ? '📻' : '🪪';
            const first  = (_id.first_name || _id.name || '').split(' ')[0];
            el.innerHTML = `
                <span style="font-size:10px;color:var(--muted,#4a6080)">On as:</span>
                <button onclick="FC_ID.showPicker()" title="Tap to change" style="
                    cursor:pointer;font-family:var(--font-hd,'Arial Narrow'),sans-serif;
                    font-size:12px;color:var(--eoc,#1a3a6b);padding:4px 10px;
                    border-radius:4px;border:1px solid var(--line,#b0c4dc);
                    background:var(--input-bg,#f7faff);
                    display:inline-flex;align-items:center;gap:5px;letter-spacing:0.05em;">
                  ${icon} <strong>${esc(disp)}</strong>
                  <span style="color:var(--muted,#4a6080);font-size:10px">${esc(first)}</span>
                </button>`;
        } else {
            el.innerHTML = `
                <button onclick="FC_ID.showPicker()" style="
                    background:var(--eoc,#1a3a6b);color:#fff;border:none;
                    border-radius:5px;padding:5px 12px;font-size:11px;
                    cursor:pointer;font-family:var(--font-hd,'Arial Narrow'),sans-serif;
                    letter-spacing:0.08em;">
                  🪪 &nbsp;IDENTIFY YOURSELF
                </button>`;
        }
    }

    // ── Init ──────────────────────────────────────────────────────────────────
    async function init() {
        load();
        await fetchRoster();
        renderBadge();
        if (!_id) setTimeout(() => { if (!_picker) showPicker(); }, 900);
    }

    async function showPicker() {
        if (_roster.length === 0) await fetchRoster();
        buildPicker();
    }

    // ── Public API ────────────────────────────────────────────────────────────
    return {
        init, showPicker,
        getMemberId:   () => _id?.member_id      || '',
        getCallsign:   () => _id?.callsign        || '',
        getRadioId:    () => _id?.radio_id        || '',
        getDisplayId:  () => bestId(_id || {}),
        getName:       () => _id?.name            || '',
        getRole:       () => _id?.role            || 'Operator',
        getMemberType: () => _id?.member_type     || 'member',
        isHam:         () => !!(_id?.callsign),
        isVisitor:     () => ['visitor','mutual_aid'].includes(_id?.member_type),
        getIdentity:   () => _id ? { ..._id } : null,
        onSet:  fn => { _cbs.push(fn); },
        clear:  () => {
            _id = null;
            try { localStorage.removeItem(STORE_KEY); } catch(e) {}
            renderBadge();
            showPicker();
        },
    };
})();

if (document.readyState === 'loading') {
    document.addEventListener('DOMContentLoaded', FC_ID.init);
} else {
    FC_ID.init();
}
