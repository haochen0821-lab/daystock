/* ============================================================
   Daystock i18n — default: zh, switchable to en
   Elements with data-i18n="key" get their textContent replaced.
   Elements with data-i18n-ph="key" get their placeholder replaced.
   Elements with data-i18n-title="key" get their title replaced.
   ============================================================ */

const I18N = {
  /* ── Navigation (base.html) ── */
  'nav.dashboard':      { en: 'Dashboard' },
  'nav.trades':         { en: 'Trades' },
  'nav.watchlist':      { en: 'Watchlist' },
  'nav.analytics':      { en: 'Analytics' },
  'nav.simulation':     { en: 'Simulation' },
  'nav.report':         { en: 'Report' },
  'nav.dividends':      { en: 'Dividends' },
  'nav.academy':        { en: 'Academy' },
  'nav.bookmarks':      { en: 'Bookmarks' },
  'nav.portfolios':     { en: 'Portfolios' },
  'nav.journal':        { en: 'Journal' },
  'nav.settings':       { en: 'Settings' },
  'nav.admin':          { en: 'Admin' },
  'nav.logout':         { en: 'Logout' },

  /* ── Dashboard ── */
  'dash.market_barometer':   { en: 'Market Barometer' },
  'dash.word_of_day':        { en: 'Word of the Day' },
  'dash.anniversary':        { en: '1-Year Anniversary Countdown' },
  'dash.loading':            { en: 'Loading...' },
  'dash.no_word':            { en: 'No word available today' },
  'dash.no_holdings_track':  { en: 'No holdings to track' },
  'dash.fail_load':          { en: 'Failed to load' },
  'dash.concentration_warn': { en: 'Concentration Warning' },
  'dash.no_market_data':     { en: 'No market data available' },
  'dash.fail_market':        { en: 'Failed to load market data' },
  'dash.total_market_value': { en: 'Total Market Value' },
  'dash.total_cost':         { en: 'Total Cost' },
  'dash.unrealized_pl':      { en: 'Unrealized P&L' },
  'dash.holdings_count':     { en: 'Holdings Count' },
  'dash.no_holdings':        { en: 'No holdings' },
  'dash.allocation':         { en: 'Market Value Allocation' },
  'dash.pl_ranked':          { en: 'P&L % Ranked' },
  'dash.holdings_detail':    { en: 'Holdings Detail' },
  'dash.symbol':             { en: 'Symbol' },
  'dash.market':             { en: 'Market' },
  'dash.shares':             { en: 'Shares' },
  'dash.avg_cost':           { en: 'Avg Cost' },
  'dash.current_price':      { en: 'Current Price' },
  'dash.market_value':       { en: 'Market Value' },
  'dash.pl_net':             { en: 'P&L (Net)' },
  'dash.pl_pct':             { en: 'P&L%' },
  'dash.div_yield':          { en: 'Div Yield' },

  /* ── Trades ── */
  'trades.title':            { en: 'Trades' },
  'trades.total_commission': { en: 'Total Commission' },
  'trades.total_tax':        { en: 'Total Tax' },
  'trades.total_fees':       { en: 'Total Fees' },
  'trades.all':              { en: 'All' },
  'trades.buy':              { en: 'Buy' },
  'trades.sell':             { en: 'Sell' },
  'trades.filter':           { en: 'Filter' },
  'trades.add_trade':        { en: '+ Add Trade' },
  'trades.history':          { en: 'Trade History' },
  'trades.date':             { en: 'Date' },
  'trades.symbol':           { en: 'Symbol' },
  'trades.market':           { en: 'Market' },
  'trades.type':             { en: 'Type' },
  'trades.price':            { en: 'Price' },
  'trades.shares':           { en: 'Shares' },
  'trades.fees':             { en: 'Fees' },
  'trades.net_amount':       { en: 'Net Amount' },
  'trades.reason':           { en: 'Reason' },
  'trades.account':          { en: 'Account' },
  'trades.actions':          { en: 'Actions' },
  'trades.add_modal':        { en: 'Add Trade' },
  'trades.trade_type':       { en: 'Trade Type' },
  'trades.account_broker':   { en: 'Account / Broker' },
  'trades.reason_tag':       { en: 'Reason Tag' },
  'trades.note':             { en: 'Note' },
  'trades.broker_fee':       { en: 'Broker Fee (USD)' },
  'trades.fee_preview':      { en: 'Fee Preview' },
  'trades.commission':       { en: 'Commission' },
  'trades.transaction_tax':  { en: 'Transaction Tax' },
  'trades.health_premium':   { en: 'Health Premium' },
  'trades.sec_fee':          { en: 'SEC Fee' },
  'trades.cancel':           { en: 'Cancel' },
  'trades.submit':           { en: 'Submit' },
  'trades.fee_breakdown':    { en: 'Fee Breakdown' },
  'trades.close':            { en: 'Close' },
  'trades.edit_trade':       { en: 'Edit Trade' },
  'trades.edit':             { en: 'Edit' },
  'trades.delete':           { en: 'Delete' },
  'trades.save':             { en: 'Save' },
  'trades.no_trades':        { en: 'No trades found' },
  'trades.discount':         { en: 'Commission Discount' },

  /* ── Watchlist ── */
  'watch.title':             { en: 'Watchlist' },
  'watch.add':               { en: 'Add' },
  'watch.empty':             { en: 'No stocks in your watchlist yet. Add one above to get started.' },
  'watch.k_line':            { en: 'K Line' },
  'watch.return_line':       { en: 'Return Line' },

  /* ── Analytics ── */
  'analytics.title':         { en: 'Analytics' },
  'analytics.win_rate':      { en: 'Win Rate Stats' },
  'analytics.heatmap':       { en: 'Monthly P&L Heatmap' },
  'analytics.hold_days':     { en: 'Hold Days Analysis' },
  'analytics.fx_overview':   { en: 'FX Rate Overview' },
  'analytics.multi_compare': { en: 'Multi-Symbol Compare' },
  'analytics.reason_wr':     { en: 'Reason Win Rate' },
  'analytics.loading':       { en: 'Loading...' },
  'analytics.closed_trades': { en: 'Closed Trade Details' },
  'analytics.symbol':        { en: 'Symbol' },
  'analytics.market':        { en: 'Market' },
  'analytics.buy_price':     { en: 'Buy Price' },
  'analytics.sell_price':    { en: 'Sell Price' },
  'analytics.shares':        { en: 'Shares' },
  'analytics.pl':            { en: 'P&L' },
  'analytics.return_pct':    { en: 'Return%' },
  'analytics.hold_days_col': { en: 'Hold Days' },
  'analytics.sell_date':     { en: 'Sell Date' },
  'analytics.no_data':       { en: 'No data available' },
  'analytics.monthly_pl':    { en: 'Monthly P&L' },
  'analytics.hold_range':    { en: 'Hold Days Range Stats' },
  'analytics.trade_count':   { en: 'Trades:' },
  'analytics.win_rate_pct':  { en: 'Win Rate:' },
  'analytics.avg_return':    { en: 'Avg Return:' },
  'analytics.hold_vs_ret':   { en: 'Hold Days vs Return%' },
  'analytics.profit':        { en: 'Profit' },
  'analytics.loss':          { en: 'Loss' },
  'analytics.usd_twd':       { en: 'USD / TWD Rate' },
  'analytics.twd_base':      { en: 'TWD Base' },
  'analytics.usd_base':      { en: 'USD Base' },
  'analytics.cost':          { en: 'Cost' },
  'analytics.mkt_val':       { en: 'Market Value' },
  'analytics.total_cost':    { en: 'Total Cost (TWD)' },
  'analytics.total_mktval':  { en: 'Total Market Value (TWD)' },
  'analytics.total_pl':      { en: 'Total P&L (TWD)' },
  'analytics.compare_btn':   { en: 'Compare' },
  'analytics.analyzing':     { en: 'Analyzing...' },
  'analytics.compare_chart': { en: 'Multi-Symbol Return Compare (Base=100)' },
  'analytics.rank':          { en: 'Rank' },
  'analytics.total_return':  { en: 'Total Return%' },
  'analytics.reason_detail': { en: 'Reason Tag Details' },
  'analytics.reason_tag':    { en: 'Reason Tag' },
  'analytics.avg_hold_days': { en: 'Avg Hold Days' },
  'analytics.total_pl_col':  { en: 'Total P&L' },
  'analytics.tw_stock':      { en: 'TW Stocks' },
  'analytics.us_stock':      { en: 'US Stocks' },
  'analytics.wr_compare':    { en: 'TW vs US Win Rate Compare' },
  'analytics.fail_load':     { en: 'Failed to load' },

  /* ── Simulation ── */
  'sim.title':               { en: 'Simulation' },
  'sim.fixed_shares':        { en: 'Fixed Shares' },
  'sim.fixed_amount':        { en: 'Fixed Amount' },
  'sim.dca':                 { en: 'DCA' },
  'sim.custom':              { en: 'Custom' },
  'sim.drip':                { en: 'DRIP' },
  'sim.symbol':              { en: 'Symbol' },
  'sim.market':              { en: 'Market' },
  'sim.shares':              { en: 'Shares' },
  'sim.start_date':          { en: 'Start Date' },
  'sim.end_date':            { en: 'End Date' },
  'sim.run':                 { en: 'Run Simulation' },
  'sim.amount_per_buy':      { en: 'Amount per Buy' },
  'sim.frequency':           { en: 'Frequency (days)' },
  'sim.amount':              { en: 'Amount' },
  'sim.trade_list':          { en: 'Trade List' },
  'sim.date':                { en: 'Date' },
  'sim.type':                { en: 'Type' },
  'sim.add_trade':           { en: '+ Add Trade' },
  'sim.run_drip':            { en: 'Run DRIP Simulation' },
  'sim.results':             { en: 'Results' },
  'sim.gross_return':        { en: 'Gross Return' },
  'sim.net_return':          { en: 'Net Return' },
  'sim.cagr':                { en: 'CAGR' },
  'sim.max_drawdown':        { en: 'Max Drawdown' },
  'sim.vs_benchmark':        { en: 'vs Benchmark' },
  'sim.net_pl':              { en: 'Net P&L' },
  'sim.market_value':        { en: 'Market Value' },
  'sim.cost':                { en: 'Cost' },
  'sim.benchmark':           { en: 'Benchmark' },

  /* ── Report ── */
  'report.title':            { en: 'Report' },
  'report.realized_pl':      { en: 'Realized P&L Report' },
  'report.desc':             { en: 'FIFO-matched trade analysis across multiple dimensions' },
  'report.trade_details':    { en: 'Trade Details' },
  'report.by_year':          { en: 'By Year' },
  'report.by_account':       { en: 'By Account' },
  'report.by_reason':        { en: 'By Reason Tag' },
  'report.year':             { en: 'Year' },
  'report.market':           { en: 'Market' },
  'report.account':          { en: 'Account' },
  'report.reason_tag':       { en: 'Reason Tag' },
  'report.profit_loss':      { en: 'Profit / Loss' },
  'report.all':              { en: 'All' },
  'report.profit_only':      { en: 'Profit Only' },
  'report.loss_only':        { en: 'Loss Only' },
  'report.apply':            { en: 'Apply' },
  'report.filtered_pl':      { en: 'Filtered P&L:' },
  'report.no_realized':      { en: 'No realized trades found.' },
  'report.symbol':           { en: 'Symbol' },
  'report.buy_date':         { en: 'Buy Date' },
  'report.sell_date':        { en: 'Sell Date' },
  'report.shares':           { en: 'Shares' },
  'report.buy_price':        { en: 'Buy Price' },
  'report.sell_price':       { en: 'Sell Price' },
  'report.fees':             { en: 'Fees' },
  'report.realized_pl_col':  { en: 'Realized P&L' },
  'report.return_pct':       { en: 'Return%' },
  'report.hold_days':        { en: 'Hold Days' },
  'report.reason':           { en: 'Reason' },
  'report.actions':          { en: 'Actions' },
  'report.edit':             { en: 'Edit' },
  'report.no_data':          { en: 'No data available.' },
  'report.tax_title':        { en: 'Year-End Tax Filing Reminder' },
  'report.cancel':           { en: 'Cancel' },
  'report.save':             { en: 'Save' },

  /* ── Dividends ── */
  'div.title':               { en: 'Dividends' },
  'div.upcoming':            { en: 'Upcoming Dividends' },
  'div.add':                 { en: 'Add Dividend' },
  'div.auto_fetch':          { en: 'Auto Fetch' },
  'div.fetching':            { en: 'Fetching...' },
  'div.fetch_failed':        { en: 'Fetch failed' },
  'div.ex_date':             { en: 'Ex-Date' },
  'div.amount_per_share':    { en: 'Amount (per share)' },
  'div.remind_days':         { en: 'Remind Days Before' },
  'div.health_calc':         { en: 'TW Health Premium Calculator' },
  'div.health_desc':         { en: 'If total dividend income ≥ NT$20,000, a 2.11% supplementary health premium applies.' },
  'div.shares_held':         { en: 'Shares Held' },
  'div.div_per_share':       { en: 'Dividend Per Share (NT$)' },
  'div.total_income':        { en: 'Total Dividend Income' },
  'div.health_prem':         { en: 'Health Premium (2.11%)' },
  'div.below_threshold':     { en: 'Below NT$20,000 threshold - no premium' },
  'div.us_tax_title':        { en: 'US Dividend Tax Info' },
  'div.withholding':         { en: '30% Withholding Tax' },
  'div.all_dividends':       { en: 'All Dividends' },
  'div.refresh':             { en: 'Refresh' },
  'div.amount':              { en: 'Amount' },
  'div.remind':              { en: 'Remind' },
  'div.status':              { en: 'Status' },
  'div.actions':             { en: 'Actions' },
  'div.delete':              { en: 'Delete' },
  'div.no_dividends':        { en: 'No dividends recorded yet' },
  'div.today':               { en: 'Today!' },
  'div.upcoming_badge':      { en: 'Upcoming' },
  'div.future':              { en: 'Future' },
  'div.past':                { en: 'Past' },
  'div.day':                 { en: 'day' },
  'div.days':                { en: 'days' },

  /* ── Academy ── */
  'acad.title':              { en: 'Academy' },
  'acad.subtitle':           { en: 'Daystock Academy' },
  'acad.desc':               { en: 'From basic concepts to practical skills, systematically learn stock investment knowledge.' },
  'acad.all':                { en: 'All' },
  'acad.concept':            { en: 'Concept' },
  'acad.glossary':           { en: 'Glossary' },
  'acad.abbreviation':       { en: 'Abbreviation' },
  'acad.practical':          { en: 'Practical Tips' },
  'acad.no_articles':        { en: 'No articles found matching your criteria' },
  'acad.manage':             { en: 'Manage' },
  'acad.back':               { en: '← Back to Academy' },
  'acad.edit':               { en: 'Edit' },
  'acad.bookmark':           { en: 'Bookmark' },
  'acad.bookmark_to':        { en: 'Bookmark to folder' },
  'acad.no_content':         { en: 'This article has no content yet.' },
  'acad.fail_load':          { en: 'Failed to load article content.' },
  'acad.write_note':         { en: 'Write Note' },
  'acad.edit_note':          { en: 'Edit Note' },
  'acad.cancel':             { en: 'Cancel' },
  'acad.save':               { en: 'Save' },

  /* ── Academy Manage ── */
  'acad_mgr.title':          { en: 'Academy Manage' },
  'acad_mgr.article_mgmt':   { en: 'Article Management' },
  'acad_mgr.drag_sort':      { en: 'Drag Sort' },
  'acad_mgr.articles':       { en: 'Articles' },
  'acad_mgr.new':            { en: '+ New' },
  'acad_mgr.loading':        { en: 'Loading...' },
  'acad_mgr.title_field':    { en: 'Title' },
  'acad_mgr.category':       { en: 'Category' },
  'acad_mgr.tags':           { en: 'Tags (comma separated)' },
  'acad_mgr.publish_now':    { en: 'Publish immediately' },
  'acad_mgr.summary':        { en: 'Summary' },
  'acad_mgr.content':        { en: 'Content' },
  'acad_mgr.save':           { en: 'Save' },
  'acad_mgr.cancel':         { en: 'Cancel' },
  'acad_mgr.delete':         { en: 'Delete' },
  'acad_mgr.no_articles':    { en: 'No articles yet.' },

  /* ── Bookmarks ── */
  'bm.title':                { en: 'My Bookmarks' },
  'bm.all':                  { en: 'ALL' },
  'bm.empty':                { en: 'No bookmarks found. Browse the Academy to add some!' },
  'bm.write_note':           { en: 'Write Note' },
  'bm.edit_note':            { en: 'Edit Note' },
  'bm.has_note':             { en: 'Has Note' },
  'bm.cancel':               { en: 'Cancel' },
  'bm.save':                 { en: 'Save' },
  'bm.remove':               { en: 'Remove' },

  /* ── Portfolios ── */
  'port.title':              { en: 'Portfolios' },
  'port.create':             { en: '+ Create Portfolio' },
  'port.empty':              { en: 'No portfolios yet. Create one to group and compare your stocks.' },
  'port.create_modal':       { en: 'Create Portfolio' },
  'port.name':               { en: 'Name' },
  'port.description':        { en: 'Description' },
  'port.tags':               { en: 'Tags' },
  'port.add_tag':            { en: '+ Add Tag' },
  'port.cancel':             { en: 'Cancel' },
  'port.create_btn':         { en: 'Create' },
  'port.edit_modal':         { en: 'Edit Portfolio' },
  'port.save':               { en: 'Save' },
  'port.members':            { en: 'members' },
  'port.back':               { en: '← Back to Portfolios' },
  'port.add_member':         { en: '+ Add Member' },
  'port.overview':           { en: 'Overview' },
  'port.trend':              { en: 'Trend Compare' },
  'port.news':               { en: 'News' },
  'port.symbol':             { en: 'Symbol' },
  'port.market':             { en: 'Market' },
  'port.price':              { en: 'Price' },
  'port.change_pct':         { en: 'Change %' },
  'port.allocation':         { en: 'Market Value Allocation' },
  'port.loading':            { en: 'Loading...' },
  'port.fail_quotes':        { en: 'Failed to load quotes.' },
  'port.no_members':         { en: 'No members yet. Add stocks from your watchlist.' },
  'port.all_symbols':        { en: 'All Symbols' },
  'port.loading_news':       { en: 'Loading news...' },
  'port.fail_news':          { en: 'Failed to load news.' },
  'port.no_news':            { en: 'No news found.' },
  'port.record_trade':       { en: 'Record as News Trade' },
  'port.loading_watchlist':  { en: 'Loading watchlist...' },
  'port.empty_watchlist':    { en: 'Your watchlist is empty. Add stocks to your watchlist first.' },
  'port.already_added':      { en: 'Already Added' },
  'port.add':                { en: 'Add' },
  'port.adding':             { en: 'Adding...' },
  'port.add_from_watchlist': { en: 'Add Member from Watchlist' },
  'port.close':              { en: 'Close' },

  /* ── Journal ── */
  'journal.title':           { en: 'Journal' },
  'journal.today':           { en: 'Today' },
  'journal.sun':             { en: 'Sun' },
  'journal.mon':             { en: 'Mon' },
  'journal.tue':             { en: 'Tue' },
  'journal.wed':             { en: 'Wed' },
  'journal.thu':             { en: 'Thu' },
  'journal.fri':             { en: 'Fri' },
  'journal.sat':             { en: 'Sat' },
  'journal.select_date':     { en: 'Select a date to write' },
  'journal.mood':            { en: 'Mood' },
  'journal.very_good':       { en: 'Very Good' },
  'journal.nice':            { en: 'Nice' },
  'journal.neutral':         { en: 'Neutral' },
  'journal.bad':             { en: 'Bad' },
  'journal.terrible':        { en: 'Terrible' },
  'journal.market_view':     { en: 'Market View' },
  'journal.bullish':         { en: 'Bullish' },
  'journal.bear_neutral':    { en: 'Neutral' },
  'journal.bearish':         { en: 'Bearish' },
  'journal.content':         { en: 'Content' },
  'journal.save':            { en: 'Save' },
  'journal.delete':          { en: 'Delete' },

  /* ── Settings ── */
  'set.title':               { en: 'Settings' },
  'set.profile':             { en: 'Profile Info' },
  'set.trading_pref':        { en: 'Trading Preferences' },
  'set.default_market':      { en: 'Default Market' },
  'set.commission_discount': { en: 'Commission Discount' },
  'set.no_discount':         { en: 'No discount' },
  'set.concentration':       { en: 'Concentration Threshold (%)' },
  'set.anniversary':         { en: 'Anniversary Countdown (US Stock Tax Reminder)' },
  'set.save_pref':           { en: 'Save Preferences' },
  'set.change_pw':           { en: 'Change Password' },
  'set.current_pw':          { en: 'Current Password' },
  'set.new_pw':              { en: 'New Password' },
  'set.confirm_pw':          { en: 'Confirm New Password' },
  'set.pw_strength':         { en: 'Password Strength' },
  'set.pw_match':            { en: 'Passwords match' },
  'set.pw_no_match':         { en: 'Passwords do not match' },
  'set.change_pw_btn':       { en: 'Change Password' },
  'set.pref_saved':          { en: 'Preferences saved successfully.' },
  'set.pref_fail':           { en: 'Failed to save.' },
  'set.pw_changed':          { en: 'Password changed successfully.' },
  'set.pw_fail':             { en: 'Failed to change password.' },

  /* ── Admin ── */
  'admin.title':             { en: 'Admin' },
  'admin.total_users':       { en: 'Total Users' },
  'admin.active_users':      { en: 'Active Users' },
  'admin.user_mgmt':         { en: 'User Management' },
  'admin.id':                { en: 'ID' },
  'admin.username':          { en: 'Username' },
  'admin.email':             { en: 'Email' },
  'admin.role':              { en: 'Role' },
  'admin.status':            { en: 'Status' },
  'admin.created':           { en: 'Created' },
  'admin.actions':           { en: 'Actions' },
  'admin.disable':           { en: 'Disable' },
  'admin.enable':            { en: 'Enable' },
  'admin.loading':           { en: 'Loading...' },
  'admin.no_users':          { en: 'No users found.' },

  /* ── Common ── */
  'common.cancel':           { en: 'Cancel' },
  'common.save':             { en: 'Save' },
  'common.delete':           { en: 'Delete' },
  'common.close':            { en: 'Close' },
  'common.loading':          { en: 'Loading...' },
  'common.edit':             { en: 'Edit' },
  'common.submit':           { en: 'Submit' },
  'common.optional':         { en: 'optional' },

  /* ── Login / Register ── */
  'login.subtitle':          { en: 'smart trading terminal' },
  'login.username':          { en: 'Username' },
  'login.password':          { en: 'Password' },
  'login.sign_in':           { en: 'Sign In' },
  'login.signing_in':        { en: 'Signing in...' },
  'login.no_account':        { en: 'No account?' },
  'login.create_one':        { en: 'Create one' },
  'login.network_error':     { en: 'Network error. Please try again.' },
  'login.fail':              { en: 'Login failed.' },
  'reg.title':               { en: 'Create Account' },
  'reg.subtitle':            { en: 'join Daystock' },
  'reg.email':               { en: 'Email' },
  'reg.min_8':               { en: 'Minimum 8 characters' },
  'reg.create_btn':          { en: 'Create Account' },
  'reg.creating':            { en: 'Creating account...' },
  'reg.has_account':         { en: 'Already have an account?' },
  'reg.sign_in':             { en: 'Sign in' },
  'reg.good':                { en: 'Good' },
  'reg.strong':              { en: 'Strong' },
  'reg.network_error':       { en: 'Network error. Please try again.' },
  'reg.fail':                { en: 'Registration failed.' },
};

/* ── zh (Chinese) default text — stored for switching back from en ── */
const ZH = {};

function _getLang() {
  return localStorage.getItem('ds-lang') || 'zh';
}

function _setLang(lang) {
  localStorage.setItem('ds-lang', lang);
}

/* Capture original zh text on first run */
function _captureZh() {
  document.querySelectorAll('[data-i18n]').forEach(function(el) {
    var key = el.getAttribute('data-i18n');
    if (!ZH[key]) ZH[key] = el.textContent;
  });
  document.querySelectorAll('[data-i18n-ph]').forEach(function(el) {
    var key = el.getAttribute('data-i18n-ph');
    if (!ZH['ph:' + key]) ZH['ph:' + key] = el.placeholder;
  });
  document.querySelectorAll('[data-i18n-title]').forEach(function(el) {
    var key = el.getAttribute('data-i18n-title');
    if (!ZH['ti:' + key]) ZH['ti:' + key] = el.title;
  });
}

function applyLang(lang) {
  _setLang(lang);
  document.querySelectorAll('[data-i18n]').forEach(function(el) {
    var key = el.getAttribute('data-i18n');
    if (lang === 'en' && I18N[key]) {
      el.textContent = I18N[key].en;
    } else if (lang === 'zh' && ZH[key]) {
      el.textContent = ZH[key];
    }
  });
  document.querySelectorAll('[data-i18n-ph]').forEach(function(el) {
    var key = el.getAttribute('data-i18n-ph');
    if (lang === 'en' && I18N[key]) {
      el.placeholder = I18N[key].en;
    } else if (lang === 'zh' && ZH['ph:' + key]) {
      el.placeholder = ZH['ph:' + key];
    }
  });
  document.querySelectorAll('[data-i18n-title]').forEach(function(el) {
    var key = el.getAttribute('data-i18n-title');
    if (lang === 'en' && I18N[key]) {
      el.title = I18N[key].en;
    } else if (lang === 'zh' && ZH['ti:' + key]) {
      el.title = ZH['ti:' + key];
    }
  });

  /* Update toggle button */
  var btn = document.getElementById('langToggle');
  if (btn) btn.textContent = lang === 'zh' ? 'EN' : '中';

  document.documentElement.lang = lang === 'zh' ? 'zh-Hant' : 'en';
}

function toggleLang() {
  applyLang(_getLang() === 'zh' ? 'en' : 'zh');
}

/* ── Theme ── */
function _getTheme() {
  return localStorage.getItem('ds-theme') || 'light';
}

function applyTheme(theme) {
  localStorage.setItem('ds-theme', theme);
  document.body.classList.remove('theme-light', 'theme-dark');
  document.body.classList.add('theme-' + theme);
  var btn = document.getElementById('themeToggle');
  if (btn) btn.textContent = theme === 'dark' ? '\u2600' : '\u263E';

  /* Update meta theme-color */
  var meta = document.querySelector('meta[name="theme-color"]');
  if (meta) meta.content = theme === 'dark' ? '#0a0f1e' : '#f5f7fa';
}

function toggleTheme() {
  applyTheme(_getTheme() === 'light' ? 'dark' : 'light');
}

/* ── Init ── */
function initI18n() {
  _captureZh();
  var lang = _getLang();
  if (lang === 'en') applyLang('en');
  else applyLang('zh');

  applyTheme(_getTheme());
}

document.addEventListener('DOMContentLoaded', initI18n);
