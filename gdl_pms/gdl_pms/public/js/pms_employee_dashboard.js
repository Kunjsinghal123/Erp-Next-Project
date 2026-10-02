frappe.provide('gdl_pms.dashboard');

// Global trigger to evaluate all PMS dashboards across route changes
if (!window.gdl_pms) window.gdl_pms = {};
if (!gdl_pms.trigger_all_dashboards) {
    gdl_pms.trigger_all_dashboards = function () {
        var run = function () {
            if (window.gdl_pms) {
                if (gdl_pms.dashboard) gdl_pms.dashboard.check_and_render();
                if (gdl_pms.supervisor_dashboard) gdl_pms.supervisor_dashboard.check_and_render();
                if (gdl_pms.reviewer_dashboard) gdl_pms.reviewer_dashboard.check_and_render();
                if (gdl_pms.supervisor_2_dashboard) gdl_pms.supervisor_2_dashboard.check_and_render();
                if (gdl_pms.hr_dashboard) gdl_pms.hr_dashboard.check_and_render();
            }
        };
        run();
        [20, 80, 200, 500, 1000].forEach(function (delay) {
            setTimeout(run, delay);
        });
    };
}

// Monkey-patch Frappe Workspace show_page so PMS dashboards trigger on page load
$(document).ready(function () {
    if (window.frappe && frappe.views && frappe.views.Workspace && !frappe.views.Workspace._pms_patched) {
        frappe.views.Workspace._pms_patched = true;
        var _orig_show_page = frappe.views.Workspace.prototype.show_page;
        frappe.views.Workspace.prototype.show_page = async function (page) {
            var res = await _orig_show_page.call(this, page);
            gdl_pms.trigger_all_dashboards();
            return res;
        };
    }
});

$(document).on('app_ready page-change workspace_rendered', function () {
    gdl_pms.trigger_all_dashboards();
});

frappe.router.on('change', function () {
    gdl_pms.trigger_all_dashboards();
});

gdl_pms.dashboard = {
    init: function () {
        this.schedule_checks();
    },

    schedule_checks: function () {
        gdl_pms.trigger_all_dashboards();
    },

    is_employee_workspace: function () {
        var route = frappe.get_route() || [];
        if (!route.length) return false;
        var first = (route[0] || '').toLowerCase();
        if (['form', 'list', 'query-report', 'report', 'tree', 'print', 'modules', 'view'].indexOf(first) !== -1) {
            return false;
        }

        var full_route = (route || []).join('/').toLowerCase();
        if (full_route.indexOf('supervisor') !== -1 || full_route.indexOf('reviewer') !== -1 || full_route.indexOf('hr') !== -1 || full_route.indexOf('admin') !== -1) {
            return false;
        }

        var hash = (window.location.hash || '').toLowerCase();
        var pathname = (window.location.pathname || '').toLowerCase();
        var combined = full_route + ' ' + hash + ' ' + pathname;

        return combined.indexOf('pms') !== -1 && combined.indexOf('employee') !== -1;
    },

    get_container: function () {
        var $editor = $('.editor-js-container:visible').first();
        if ($editor.length) return $editor;
        var $ws = $('.workspace-page:visible').first();
        if ($ws.length) return $ws;
        var $main = $('.layout-main-section:visible').first();
        if ($main.length) return $main;
        return null;
    },

    check_and_render: function () {
        var self = this;
        if (!self.is_employee_workspace()) {
            $('[data-pms-dashboard="employee"]').remove();
            $('body, .layout-main-section, .workspace-page').removeClass('gdl-pms-employee-dashboard-active');
            return;
        }

        // We are on Employee Workspace: Purge any foreign PMS dashboards
        $('.gdl-pms-dashboard-wrapper:not([data-pms-dashboard="employee"]), .gdl-pms-supervisor-2-wrapper:not([data-pms-dashboard="employee"])').remove();

        $('body, .layout-main-section, .workspace-page')
            .removeClass('gdl-pms-supervisor-dashboard-active gdl-pms-reviewer-dashboard-active gdl-pms-supervisor-2-dashboard-active gdl-pms-hr-dashboard-active')
            .addClass('gdl-pms-custom-dashboard-active gdl-pms-employee-dashboard-active');

        var $container = self.get_container();
        if (!$container || !$container.length) return;

        if ($container.find('[data-pms-dashboard="employee"]').length > 0) {
            $container.children().not('[data-pms-dashboard="employee"]').hide();
            return;
        }

        self.render_dashboard($container);
    },

    render_dashboard: function ($container) {
        var self = this;
        if (!self.is_employee_workspace()) return;

        $container.children().not('[data-pms-dashboard="employee"]').hide();

        // Force parent containers to stretch 100% width
        $container.parents('.container, .page-body, .layout-main-section, .page-content, .layout-main-section-wrapper').css({
            'max-width': '100%',
            'width': '100%',
            'padding-left': '0',
            'padding-right': '0',
            'margin-left': '0',
            'margin-right': '0'
        });

        var $wrapper = $container.find('[data-pms-dashboard="employee"]');
        if (!$wrapper.length) {
            $wrapper = $(`
                <div class="gdl-pms-dashboard-wrapper" data-pms-dashboard="employee">
                    <div style="padding: 60px 20px; text-align: center; color: var(--text-muted);">
                        <div class="spinner-border text-primary" role="status" style="width: 2rem; height: 2rem;"></div>
                        <div style="margin-top: 12px; font-size: 14px; font-weight: 500;">Loading Employee Dashboard...</div>
                    </div>
                </div>
            `).appendTo($container);
        }

        frappe.call({
            method: 'gdl_pms.dashboard_api.get_employee_dashboard_data',
            callback: function (r) {
                if (!self.is_employee_workspace()) {
                    $('[data-pms-dashboard="employee"]').remove();
                    return;
                }
                if (r.message) {
                    var html = self.build_dashboard_html(r.message);
                    var $newWrapper = $(html);
                    $newWrapper.attr('data-pms-dashboard', 'employee');
                    if ($wrapper && $wrapper.parent().length) {
                        $wrapper.replaceWith($newWrapper);
                    } else {
                        $container.append($newWrapper);
                    }
                    $container.children().not('[data-pms-dashboard="employee"]').hide();
                    self.bind_events($container, r.message);
                }
            }
        });
    },

    get_activity_icon: function (status) {
        if (status === 'Approved') {
            return `<svg width="14" height="14" viewBox="0 0 24 24" fill="none" stroke="currentColor" stroke-width="2.5"><polyline points="20 6 9 17 4 12"/></svg>`;
        }
        if (status === 'Rejected' || status === 'Returned') {
            return `<svg width="14" height="14" viewBox="0 0 24 24" fill="none" stroke="currentColor" stroke-width="2.5"><line x1="18" y1="6" x2="6" y2="18"/><line x1="6" y1="6" x2="18" y2="18"/></svg>`;
        }
        return `<svg width="14" height="14" viewBox="0 0 24 24" fill="none" stroke="currentColor" stroke-width="2.5"><circle cx="12" cy="12" r="10"/><line x1="12" y1="8" x2="12" y2="12"/><line x1="12" y1="16" x2="12.01" y2="16"/></svg>`;
    },

    build_dashboard_html: function (data) {
        var counts = data.counts || { my_plans: 0, active_cycles: 0, amendments: 0, approval_history: 0 };
        var activities = data.recent_activities || [];
        var cycles = data.cycles || [];

        // Build Active Cycles HTML (matching HR Admin view)
        var cycles_html = '';
        if (cycles.length === 0) {
            cycles_html = `
                <div class="pms-empty-activity">
                    <p class="text-muted">No appraisal cycles found.</p>
                </div>
            `;
        } else {
            cycles.forEach(function (c) {
                cycles_html += `
                    <div class="pms-activity-row" data-action="route-cycle" data-name="${frappe.utils.escape_html(c.name)}">
                        <div class="pms-activity-icon ${c.badge_class}">
                            <svg width="18" height="18" viewBox="0 0 24 24" fill="none" stroke="#0d9488" stroke-width="2.5">
                                <circle cx="12" cy="12" r="10"></circle>
                                <polyline points="12 6 12 12 16 14"></polyline>
                            </svg>
                        </div>
                        <div class="pms-activity-details">
                            <div class="pms-activity-title">${frappe.utils.escape_html(c.title)}</div>
                            <div class="pms-activity-subtitle">${frappe.utils.escape_html(c.subtitle)}</div>
                        </div>
                        <div class="pms-activity-status">
                            <span class="pms-badge ${c.badge_class}">${frappe.utils.escape_html(c.status)}</span>
                        </div>
                    </div>
                `;
            });
        }

        // Build Recent Activity HTML
        var activity_html = '';
        if (activities.length === 0) {
            activity_html = `
                <div class="pms-empty-activity">
                    <p class="text-muted">No recent activity found.</p>
                </div>
            `;
        } else {
            activities.forEach(function (act) {
                var icon_svg = gdl_pms.dashboard.get_activity_icon(act.status);
                activity_html += `
                    <div class="pms-activity-row" data-doctype="${act.doctype}" data-name="${act.name}">
                        <div class="pms-activity-icon ${act.badge_class}">
                            ${icon_svg}
                        </div>
                        <div class="pms-activity-details">
                            <div class="pms-activity-title">${frappe.utils.escape_html(act.title)}</div>
                            <div class="pms-activity-subtitle">${frappe.utils.escape_html(act.date_str)}</div>
                        </div>
                        <div class="pms-activity-status">
                            <span class="pms-badge ${act.badge_class}">${frappe.utils.escape_html(act.status)}</span>
                        </div>
                    </div>
                `;
            });
        }

        // Build Cycle Options
        var cycle_options_html = '<option value="">Current Cycle</option>';
        cycles.forEach(function (c) {
            cycle_options_html += `<option value="${frappe.utils.escape_html(c.name)}">${frappe.utils.escape_html(c.cycle_name || c.name)}</option>`;
        });

        // return `
        // <div class="gdl-pms-dashboard-wrapper" data-pms-dashboard="employee">
        //     <!-- Top Greeting & Header Section -->
        //     <div class="pms-header-row">
        //         <div class="pms-greeting-col">
        //             <h1 class="pms-greeting-title">${frappe.utils.escape_html(data.greeting)} 👋</h1>
        //             <p class="pms-greeting-subtitle">Manage your performance journey all in one place.</p>
        //         </div>
        //         <div class="pms-quote-col">
        //             <div class="pms-quote-text">"Progress, not perfection, leads to great results."</div>
        //             <div class="pms-quote-line"></div>
        //         </div>
        //     </div>

        //     <!-- Top 4 Stat Cards Row -->
        //     <div class="pms-stats-grid pms-stats-4col">
        //         <!-- Card 1: My Performance Plans -->
        //         <div class="pms-stat-card card-blue" data-action="route-plans">
        //             <div class="pms-stat-card-header">
        //                 <div class="pms-icon-box box-blue">
        //                     <svg width="22" height="22" viewBox="0 0 24 24" fill="none" stroke="#2563eb" stroke-width="2" stroke-linecap="round" stroke-linejoin="round">
        //                         <path d="M14 2H6a2 2 0 0 0-2 2v16a2 2 0 0 0 2 2h12a2 2 0 0 0 2-2V8z"></path>
        //                         <polyline points="14 2 14 8 20 8"></polyline>
        //                         <line x1="16" y1="13" x2="8" y2="13"></line>
        //                         <line x1="16" y1="17" x2="8" y2="17"></line>
        //                     </svg>
        //                 </div>
        //                 <div class="pms-stat-card-content">
        //                     <span class="pms-stat-title">My Plans</span>
        //                     <span class="pms-stat-arrow-top">↗</span>
        //                 </div>
        //             </div>
        //             <div class="pms-stat-number-row">
        //                 <span class="pms-stat-number">${counts.my_plans}</span>
        //                 <button class="pms-circle-arrow-btn" aria-label="Open Plans">
        //                     <svg width="14" height="14" viewBox="0 0 24 24" fill="none" stroke="currentColor" stroke-width="2.5">
        //                         <path d="M9 18l6-6-6-6"/>
        //                     </svg>
        //                 </button>
        //             </div>
        //             <div class="pms-stat-subtext">Active plans and goals</div>
        //         </div>

        //         <!-- Card 2: Active Cycles -->
        //         <div class="pms-stat-card card-teal" data-action="route-cycles">
        //             <div class="pms-stat-card-header">
        //                 <div class="pms-icon-box box-teal">
        //                     <svg width="20" height="20" viewBox="0 0 24 24" fill="none" stroke="#0d9488" stroke-width="2">
        //                         <circle cx="12" cy="12" r="10"></circle>
        //                         <polyline points="12 6 12 12 16 14"></polyline>
        //                     </svg>
        //                 </div>
        //                 <div class="pms-stat-card-content">
        //                     <span class="pms-stat-title">Appraisal Cycles</span>
        //                     <span class="pms-stat-arrow-top">↗</span>
        //                 </div>
        //             </div>
        //             <div class="pms-stat-number-row">
        //                 <span class="pms-stat-number">${counts.active_cycles || 0}</span>
        //                 <button class="pms-circle-arrow-btn" aria-label="View Cycles">
        //                     <svg width="14" height="14" viewBox="0 0 24 24" fill="none" stroke="currentColor" stroke-width="2.5">
        //                         <path d="M9 18l6-6-6-6"/>
        //                     </svg>
        //                 </button>
        //             </div>
        //             <div class="pms-stat-subtext">Active & Draft cycles</div>
        //         </div>

        //         <!-- Card 3: Plan Amendments -->
        //         <div class="pms-stat-card card-green" data-action="route-amendments">
        //             <div class="pms-stat-card-header">
        //                 <div class="pms-icon-box box-green">
        //                     <svg width="22" height="22" viewBox="0 0 24 24" fill="none" stroke="#16a34a" stroke-width="2" stroke-linecap="round" stroke-linejoin="round">
        //                         <path d="M11 4H4a2 2 0 0 0-2 2v14a2 2 0 0 0 2 2h14a2 2 0 0 0 2-2v-7"></path>
        //                         <path d="M18.5 2.5a2.121 2.121 0 0 1 3 3L12 15l-4 1 1-4 9.5-9.5z"></path>
        //                     </svg>
        //                 </div>
        //                 <div class="pms-stat-card-content">
        //                     <span class="pms-stat-title">Amendments</span>
        //                     <span class="pms-stat-arrow-top">↗</span>
        //                 </div>
        //             </div>
        //             <div class="pms-stat-number-row">
        //                 <span class="pms-stat-number">${counts.amendments}</span>
        //                 <button class="pms-circle-arrow-btn" aria-label="Open Amendments">
        //                     <svg width="14" height="14" viewBox="0 0 24 24" fill="none" stroke="currentColor" stroke-width="2.5">
        //                         <path d="M9 18l6-6-6-6"/>
        //                     </svg>
        //                 </button>
        //             </div>
        //             <div class="pms-stat-subtext">Submitted / In Progress</div>
        //         </div>

        //         <!-- Card 4: Approval History -->
        //         <div class="pms-stat-card card-purple" data-action="route-approval-history">
        //             <div class="pms-stat-card-header">
        //                 <div class="pms-icon-box box-purple">
        //                     <svg width="22" height="22" viewBox="0 0 24 24" fill="none" stroke="#9333ea" stroke-width="2" stroke-linecap="round" stroke-linejoin="round">
        //                         <circle cx="12" cy="12" r="10"></circle>
        //                         <polyline points="12 6 12 12 16 14"></polyline>
        //                     </svg>
        //                 </div>
        //                 <div class="pms-stat-card-content">
        //                     <span class="pms-stat-title">Approval History</span>
        //                     <span class="pms-stat-arrow-top">↗</span>
        //                 </div>
        //             </div>
        //             <div class="pms-stat-number-row">
        //                 <span class="pms-stat-number">${counts.approval_history}</span>
        //                 <button class="pms-circle-arrow-btn" aria-label="Open History">
        //                     <svg width="14" height="14" viewBox="0 0 24 24" fill="none" stroke="currentColor" stroke-width="2.5">
        //                         <path d="M9 18l6-6-6-6"/>
        //                     </svg>
        //                 </button>
        //             </div>
        //             <div class="pms-stat-subtext">Historical sign-offs</div>
        //         </div>
        //     </div>

        //     <!-- Middle Section: Quick Actions & Banner -->
        //     <div class="pms-mid-grid">
        //         <!-- Quick Actions Section -->
        //         <div class="pms-section-card pms-quick-actions-card">
        //             <div class="pms-section-header">
        //                 <span class="pms-section-icon">⚡</span>
        //                 <h2 class="pms-section-title">Quick Actions</h2>
        //             </div>
        //             <div class="pms-quick-actions-grid">
        //                 <div class="pms-action-tile tile-blue" data-action="new-plan">
        //                     <div class="pms-action-icon-box">
        //                         <svg width="20" height="20" viewBox="0 0 24 24" fill="none" stroke="#2563eb" stroke-width="2">
        //                             <path d="M14 2H6a2 2 0 0 0-2 2v16a2 2 0 0 0 2 2h12a2 2 0 0 0 2-2V8z"></path>
        //                             <line x1="12" y1="11" x2="12" y2="17"></line>
        //                             <line x1="9" y1="14" x2="15" y2="14"></line>
        //                         </svg>
        //                     </div>
        //                     <span class="pms-action-label">Create<br>Performance Plan</span>
        //                 </div>

        //                 <div class="pms-action-tile tile-green" data-action="new-amendment">
        //                     <div class="pms-action-icon-box">
        //                         <svg width="20" height="20" viewBox="0 0 24 24" fill="none" stroke="#16a34a" stroke-width="2">
        //                             <path d="M11 4H4a2 2 0 0 0-2 2v14a2 2 0 0 0 2 2h14a2 2 0 0 0 2-2v-7"></path>
        //                             <path d="M18.5 2.5a2.121 2.121 0 0 1 3 3L12 15l-4 1 1-4 9.5-9.5z"></path>
        //                         </svg>
        //                     </div>
        //                     <span class="pms-action-label">Request<br>Amendment</span>
        //                 </div>

        //                 <div class="pms-action-tile tile-purple" data-action="route-approval-history">
        //                     <div class="pms-action-icon-box">
        //                         <svg width="20" height="20" viewBox="0 0 24 24" fill="none" stroke="#9333ea" stroke-width="2">
        //                             <path d="M1 12s4-8 11-8 11 8 11 8-4 8-11 8-11-8-11-8z"></path>
        //                             <circle cx="12" cy="12" r="3"></circle>
        //                         </svg>
        //                     </div>
        //                     <span class="pms-action-label">View Approval<br>History</span>
        //                 </div>

        //                 <div class="pms-action-tile tile-orange" data-action="view-performance">
        //                     <div class="pms-action-icon-box">
        //                         <svg width="20" height="20" viewBox="0 0 24 24" fill="none" stroke="#ea580c" stroke-width="2">
        //                             <rect x="2" y="3" width="20" height="14" rx="2" ry="2"></rect>
        //                             <line x1="8" y1="21" x2="16" y2="21"></line>
        //                             <line x1="12" y1="17" x2="12" y2="21"></line>
        //                             <line x1="6" y1="12" x2="6" y2="10"></line>
        //                             <line x1="10" y1="12" x2="10" y2="8"></line>
        //                             <line x1="14" y1="12" x2="14" y2="6"></line>
        //                             <line x1="18" y1="12" x2="18" y2="10"></line>
        //                         </svg>
        //                     </div>
        //                     <span class="pms-action-label">View My<br>Performance</span>
        //                 </div>
        //             </div>
        //         </div>

        //         <!-- Stay Focused Banner Card -->
        //         <div class="pms-banner-card">
        //             <div class="pms-banner-bg">
        //                 <!-- SVG Graphic Background Artwork -->
        //                 <svg class="pms-banner-illustration" viewBox="0 0 400 240" fill="none" xmlns="http://www.w3.org/2000/svg">
        //                     <path d="M220 240 C280 160, 320 120, 380 90 L400 90 L400 240 Z" fill="rgba(191, 219, 254, 0.4)"/>
        //                     <path d="M180 240 C260 140, 330 100, 400 70 L400 240 Z" fill="rgba(147, 197, 253, 0.3)"/>
        //                     <circle cx="340" cy="60" r="24" fill="#FDE68A" opacity="0.9"/>
        //                     <path d="M320 70 L320 30 L345 42 L320 54" fill="#EF4444"/>
        //                     <line x1="320" y1="30" x2="320" y2="90" stroke="#475569" stroke-width="2.5" stroke-linecap="round"/>
        //                     <path d="M200 240 Q 280 200, 320 70" stroke="#ffffff" stroke-width="4" stroke-dasharray="6 6" fill="none"/>
        //                 </svg>
        //             </div>
        //             <div class="pms-banner-content">
        //                 <div class="pms-banner-badge">
        //                     <svg width="14" height="14" viewBox="0 0 24 24" fill="none" stroke="currentColor" stroke-width="2">
        //                         <circle cx="12" cy="12" r="10"></circle>
        //                         <circle cx="12" cy="12" r="6"></circle>
        //                         <circle cx="12" cy="12" r="2"></circle>
        //                     </svg>
        //                     <span>Stay Focused</span>
        //                 </div>
        //                 <h2 class="pms-banner-title">Plan. Perform. Grow.</h2>
        //                 <p class="pms-banner-desc">Track your goals, receive feedback, and achieve your best version.</p>
        //                 <button class="btn pms-btn-primary" data-action="new-plan">
        //                     Create Performance Plan &nbsp;→
        //                 </button>
        //             </div>
        //         </div>
        //     </div>

        //     <!-- Bottom Section: Active Appraisal Cycles & Recent Activity -->
        //     <div class="pms-bottom-grid">
        //         <!-- Active Appraisal Cycles Card (matching HR Admin) -->
        //         <div class="pms-section-card pms-activity-card">
        //             <div class="pms-card-header-flex">
        //                 <div class="pms-section-header">
        //                     <svg width="18" height="18" viewBox="0 0 24 24" fill="none" stroke="#475569" stroke-width="2">
        //                         <path d="M23 4v6h-6M1 20v-6h6"></path>
        //                         <path d="M3.51 9a9 9 0 0114.85-3.36L23 10M1 14l4.64 4.36A9 9 0 0020.49 15"></path>
        //                     </svg>
        //                     <h2 class="pms-section-title">Appraisal Cycles (Active & Draft)</h2>
        //                 </div>
        //                 <button class="btn btn-xs btn-default pms-btn-view-all" data-action="route-cycles">View All</button>
        //             </div>
        //             <div class="pms-activity-list">
        //                 ${cycles_html}
        //             </div>
        //         </div>

        //         <!-- Recent Activity Card -->
        //         <div class="pms-section-card pms-activity-card">
        //             <div class="pms-card-header-flex">
        //                 <div class="pms-section-header">
        //                     <span class="pms-section-icon icon-clock">🕒</span>
        //                     <h2 class="pms-section-title">Recent Activity</h2>
        //                 </div>
        //                 <button class="btn btn-xs btn-default pms-btn-view-all" data-action="route-plans">View All</button>
        //             </div>
        //             <div class="pms-activity-list">
        //                 ${activity_html}
        //             </div>
        //         </div>
        //     </div>
        // </div>
        // `;
        return `
        <div class="gdl-pms-dashboard-wrapper" data-pms-dashboard="employee">
            <!-- Top Header Section -->
            <div class="pms-header-row">
                <div class="pms-greeting-col">
                    <h1 class="pms-greeting-title">${frappe.utils.escape_html(data.greeting)}</h1>
                    <p class="pms-greeting-subtitle">Manage your performance journey all in one place.</p>
                </div>
                <div class="pms-quote-col">
                    <div class="pms-quote-text">"Progress, not perfection, leads to great results."</div>
                    <div class="pms-quote-line"></div>
                </div>
            </div>

            <!-- Top 4 Stat Cards Row -->
            <div class="pms-stats-grid pms-stats-4col">
                <!-- Card 1: My Performance Plans -->
                <div class="pms-stat-card card-blue" data-action="route-plans">
                    <div class="pms-stat-card-header">
                        <div class="pms-icon-box box-blue">
                            <svg width="20" height="20" viewBox="0 0 24 24" fill="none" stroke="#2563eb" stroke-width="2" stroke-linecap="round" stroke-linejoin="round">
                                <path d="M14 2H6a2 2 0 0 0-2 2v16a2 2 0 0 0 2 2h12a2 2 0 0 0 2-2V8z"></path>
                                <polyline points="14 2 14 8 20 8"></polyline>
                                <line x1="16" y1="13" x2="8" y2="13"></line>
                                <line x1="16" y1="17" x2="8" y2="17"></line>
                            </svg>
                        </div>
                        <span class="pms-stat-title">My Plans</span>
                    </div>
                    <div class="pms-stat-number-row">
                        <span class="pms-stat-number">${counts.my_plans}</span>
                        <button class="pms-circle-arrow-btn" aria-label="Open Plans">
                            <svg width="13" height="13" viewBox="0 0 24 24" fill="none" stroke="currentColor" stroke-width="2.5">
                                <path d="M9 18l6-6-6-6"/>
                            </svg>
                        </button>
                    </div>
                    <div class="pms-stat-subtext">Active plans and goals</div>
                </div>

                <!-- Card 2: Active Cycles -->
                <div class="pms-stat-card card-teal" data-action="route-cycles">
                    <div class="pms-stat-card-header">
                        <div class="pms-icon-box box-teal">
                            <svg width="20" height="20" viewBox="0 0 24 24" fill="none" stroke="#0d9488" stroke-width="2">
                                <circle cx="12" cy="12" r="10"></circle>
                                <polyline points="12 6 12 12 16 14"></polyline>
                            </svg>
                        </div>
                        <span class="pms-stat-title">Appraisal Cycles</span>
                    </div>
                    <div class="pms-stat-number-row">
                        <span class="pms-stat-number">${counts.active_cycles || 0}</span>
                        <button class="pms-circle-arrow-btn" aria-label="View Cycles">
                            <svg width="13" height="13" viewBox="0 0 24 24" fill="none" stroke="currentColor" stroke-width="2.5">
                                <path d="M9 18l6-6-6-6"/>
                            </svg>
                        </button>
                    </div>
                    <div class="pms-stat-subtext">Active & draft cycles</div>
                </div>

                <!-- Card 3: Plan Amendments -->
                <div class="pms-stat-card card-green" data-action="route-amendments">
                    <div class="pms-stat-card-header">
                        <div class="pms-icon-box box-green">
                            <svg width="20" height="20" viewBox="0 0 24 24" fill="none" stroke="#16a34a" stroke-width="2" stroke-linecap="round" stroke-linejoin="round">
                                <path d="M11 4H4a2 2 0 0 0-2 2v14a2 2 0 0 0 2 2h14a2 2 0 0 0 2-2v-7"></path>
                                <path d="M18.5 2.5a2.121 2.121 0 0 1 3 3L12 15l-4 1 1-4 9.5-9.5z"></path>
                            </svg>
                        </div>
                        <span class="pms-stat-title">Amendments</span>
                    </div>
                    <div class="pms-stat-number-row">
                        <span class="pms-stat-number">${counts.amendments}</span>
                        <button class="pms-circle-arrow-btn" aria-label="Open Amendments">
                            <svg width="13" height="13" viewBox="0 0 24 24" fill="none" stroke="currentColor" stroke-width="2.5">
                                <path d="M9 18l6-6-6-6"/>
                            </svg>
                        </button>
                    </div>
                    <div class="pms-stat-subtext">Submitted / in progress</div>
                </div>

                <!-- Card 4: Approval History -->
                <div class="pms-stat-card card-purple" data-action="route-approval-history">
                    <div class="pms-stat-card-header">
                        <div class="pms-icon-box box-purple">
                            <svg width="20" height="20" viewBox="0 0 24 24" fill="none" stroke="#9333ea" stroke-width="2" stroke-linecap="round" stroke-linejoin="round">
                                <circle cx="12" cy="12" r="10"></circle>
                                <polyline points="12 6 12 12 16 14"></polyline>
                            </svg>
                        </div>
                        <span class="pms-stat-title">Approval History</span>
                    </div>
                    <div class="pms-stat-number-row">
                        <span class="pms-stat-number">${counts.approval_history}</span>
                        <button class="pms-circle-arrow-btn" aria-label="Open History">
                            <svg width="13" height="13" viewBox="0 0 24 24" fill="none" stroke="currentColor" stroke-width="2.5">
                                <path d="M9 18l6-6-6-6"/>
                            </svg>
                        </button>
                    </div>
                    <div class="pms-stat-subtext">Historical sign-offs</div>
                </div>
            </div>

            <!-- Middle Section: Quick Actions & Banner -->
            <div class="pms-mid-grid">
                <!-- Quick Actions Section -->
                <div class="pms-section-card pms-quick-actions-card">
                    <div class="pms-section-header">
                        <svg width="18" height="18" viewBox="0 0 24 24" fill="none" stroke="#475569" stroke-width="2" stroke-linecap="round" stroke-linejoin="round">
                            <path d="M13 2L3 14h7l-1 8 10-12h-7l1-8z"></path>
                        </svg>
                        <h2 class="pms-section-title">Quick Actions</h2>
                    </div>
                    <div class="pms-quick-actions-grid">
                        <div class="pms-action-tile tile-blue" data-action="new-plan">
                            <div class="pms-action-icon-box">
                                <svg width="18" height="18" viewBox="0 0 24 24" fill="none" stroke="#2563eb" stroke-width="2">
                                    <path d="M14 2H6a2 2 0 0 0-2 2v16a2 2 0 0 0 2 2h12a2 2 0 0 0 2-2V8z"></path>
                                    <line x1="12" y1="11" x2="12" y2="17"></line>
                                    <line x1="9" y1="14" x2="15" y2="14"></line>
                                </svg>
                            </div>
                            <span class="pms-action-label">Create Performance Plan</span>
                        </div>

                        <div class="pms-action-tile tile-green" data-action="new-amendment">
                            <div class="pms-action-icon-box">
                                <svg width="18" height="18" viewBox="0 0 24 24" fill="none" stroke="#16a34a" stroke-width="2">
                                    <path d="M11 4H4a2 2 0 0 0-2 2v14a2 2 0 0 0 2 2h14a2 2 0 0 0 2-2v-7"></path>
                                    <path d="M18.5 2.5a2.121 2.121 0 0 1 3 3L12 15l-4 1 1-4 9.5-9.5z"></path>
                                </svg>
                            </div>
                            <span class="pms-action-label">Request Amendment</span>
                        </div>

                        <div class="pms-action-tile tile-purple" data-action="route-approval-history">
                            <div class="pms-action-icon-box">
                                <svg width="18" height="18" viewBox="0 0 24 24" fill="none" stroke="#9333ea" stroke-width="2">
                                    <path d="M1 12s4-8 11-8 11 8 11 8-4 8-11 8-11-8-11-8z"></path>
                                    <circle cx="12" cy="12" r="3"></circle>
                                </svg>
                            </div>
                            <span class="pms-action-label">View Approval History</span>
                        </div>

                        <div class="pms-action-tile tile-orange" data-action="view-performance">
                            <div class="pms-action-icon-box">
                                <svg width="18" height="18" viewBox="0 0 24 24" fill="none" stroke="#ea580c" stroke-width="2">
                                    <rect x="2" y="3" width="20" height="14" rx="2" ry="2"></rect>
                                    <line x1="8" y1="21" x2="16" y2="21"></line>
                                    <line x1="12" y1="17" x2="12" y2="21"></line>
                                    <line x1="6" y1="12" x2="6" y2="10"></line>
                                    <line x1="10" y1="12" x2="10" y2="8"></line>
                                    <line x1="14" y1="12" x2="14" y2="6"></line>
                                    <line x1="18" y1="12" x2="18" y2="10"></line>
                                </svg>
                            </div>
                            <span class="pms-action-label">View My Performance</span>
                        </div>
                    </div>
                </div>

                <!-- Stay Focused Banner Card -->
                <div class="pms-banner-card">
                    <div class="pms-banner-bg">
                        <svg class="pms-banner-illustration" viewBox="0 0 400 240" fill="none" xmlns="http://www.w3.org/2000/svg">
                            <path d="M220 240 C280 160, 320 120, 380 90 L400 90 L400 240 Z" fill="rgba(191, 219, 254, 0.4)"/>
                            <path d="M180 240 C260 140, 330 100, 400 70 L400 240 Z" fill="rgba(147, 197, 253, 0.3)"/>
                            <circle cx="340" cy="60" r="24" fill="#FDE68A" opacity="0.9"/>
                            <path d="M320 70 L320 30 L345 42 L320 54" fill="#EF4444"/>
                            <line x1="320" y1="30" x2="320" y2="90" stroke="#475569" stroke-width="2.5" stroke-linecap="round"/>
                            <path d="M200 240 Q 280 200, 320 70" stroke="#ffffff" stroke-width="4" stroke-dasharray="6 6" fill="none"/>
                        </svg>
                    </div>
                    <div class="pms-banner-content">
                        <div class="pms-banner-badge">
                            <svg width="14" height="14" viewBox="0 0 24 24" fill="none" stroke="currentColor" stroke-width="2">
                                <circle cx="12" cy="12" r="10"></circle>
                                <circle cx="12" cy="12" r="6"></circle>
                                <circle cx="12" cy="12" r="2"></circle>
                            </svg>
                            <span>Stay Focused</span>
                        </div>
                        <h2 class="pms-banner-title">Plan. Perform. Grow.</h2>
                        <p class="pms-banner-desc">Track your goals, receive feedback, and achieve your best version.</p>
                        <button class="btn pms-btn-primary" data-action="new-plan">
                            Create Performance Plan
                            <svg width="14" height="14" viewBox="0 0 24 24" fill="none" stroke="currentColor" stroke-width="2.5">
                                <path d="M5 12h14M13 6l6 6-6 6"/>
                            </svg>
                        </button>
                    </div>
                </div>
            </div>

            <!-- Bottom Section: Active Appraisal Cycles & Recent Activity -->
            <div class="pms-bottom-grid">
                <!-- Active Appraisal Cycles Card -->
                <div class="pms-section-card pms-activity-card">
                    <div class="pms-card-header-flex">
                        <div class="pms-section-header">
                            <svg width="18" height="18" viewBox="0 0 24 24" fill="none" stroke="#475569" stroke-width="2">
                                <path d="M23 4v6h-6M1 20v-6h6"></path>
                                <path d="M3.51 9a9 9 0 0114.85-3.36L23 10M1 14l4.64 4.36A9 9 0 0020.49 15"></path>
                            </svg>
                            <h2 class="pms-section-title">Appraisal Cycles (Active & Draft)</h2>
                        </div>
                        <button class="btn btn-xs btn-default pms-btn-view-all" data-action="route-cycles">View All</button>
                    </div>
                    <div class="pms-activity-list">
                        ${cycles_html}
                    </div>
                </div>

                <!-- Recent Activity Card -->
                <div class="pms-section-card pms-activity-card">
                    <div class="pms-card-header-flex">
                        <div class="pms-section-header">
                            <svg width="18" height="18" viewBox="0 0 24 24" fill="none" stroke="#475569" stroke-width="2">
                                <circle cx="12" cy="12" r="10"></circle>
                                <polyline points="12 6 12 12 16 14"></polyline>
                            </svg>
                            <h2 class="pms-section-title">Recent Activity</h2>
                        </div>
                        <button class="btn btn-xs btn-default pms-btn-view-all" data-action="route-plans">View All</button>
                    </div>
                    <div class="pms-activity-list">
                        ${activity_html}
                    </div>
                </div>
            </div>
        </div>
        `;
    },

    bind_events: function ($container, data) {
        // Handle Action Click Events
        $container.find('[data-action]').on('click', function (e) {
            e.stopPropagation();
            var action = $(this).data('action');

            if (action === 'new-plan') {
                frappe.new_doc('PMS Appraisal');
            } else if (action === 'new-amendment') {
                frappe.new_doc('PMS Plan Amendment');
            } else if (action === 'route-plans') {
                frappe.set_route('List', 'PMS Appraisal');
            } else if (action === 'route-amendments') {
                frappe.set_route('List', 'PMS Plan Amendment');
            } else if (action === 'route-approval-history') {
                frappe.set_route('List', 'PMS Appraisal', { plan_status: ['in', ['Approved', 'Rejected', 'Returned']] });
            } else if (action === 'route-cycles') {
                frappe.set_route('List', 'PMS Appraisal Cycle');
            } else if (action === 'route-cycle') {
                var cycleName = $(this).data('name');
                if (cycleName) {
                    frappe.set_route('Form', 'PMS Appraisal Cycle', cycleName);
                } else {
                    frappe.set_route('List', 'PMS Appraisal Cycle');
                }
            } else if (action === 'view-performance') {
                frappe.set_route('query-report', 'PMS Employee Report');
            }
        });

        // Click on individual Activity Rows
        $container.find('.pms-activity-row').on('click', function () {
            var action = $(this).data('action');
            var name = $(this).data('name');
            var doctype = $(this).data('doctype');

            if (action === 'route-cycle' && name) {
                frappe.set_route('Form', 'PMS Appraisal Cycle', name);
            } else if (doctype && name) {
                frappe.set_route('Form', doctype, name);
            }
        });
    }
};

function self_get_activity_icon(status) {
    var s = (status || '').toLowerCase();
    if (s.indexOf('approved') !== -1) {
        return `
            <svg width="18" height="18" viewBox="0 0 24 24" fill="none" stroke="#16a34a" stroke-width="2.5">
                <path d="M22 11.08V12a10 10 0 1 1-5.93-9.14"></path>
                <polyline points="22 4 12 14.01 9 11.01"></polyline>
            </svg>
        `;
    } else if (s.indexOf('pending') !== -1) {
        return `
            <svg width="18" height="18" viewBox="0 0 24 24" fill="none" stroke="#d97706" stroke-width="2.5">
                <path d="M11 4H4a2 2 0 0 0-2 2v14a2 2 0 0 0 2 2h14a2 2 0 0 0 2-2v-7"></path>
                <path d="M18.5 2.5a2.121 2.121 0 0 1 3 3L12 15l-4 1 1-4 9.5-9.5z"></path>
            </svg>
        `;
    } else {
        return `
            <svg width="18" height="18" viewBox="0 0 24 24" fill="none" stroke="#2563eb" stroke-width="2.5">
                <path d="M14 2H6a2 2 0 0 0-2 2v16a2 2 0 0 0 2 2h12a2 2 0 0 0 2-2V8z"></path>
                <polyline points="14 2 14 8 20 8"></polyline>
            </svg>
        `;
    }
}
window.pms_get_sidebar_icon = function (text) {
    var t = (text || '').toLowerCase();
    if (t.indexOf('calendar') !== -1 || t.indexOf('calender') !== -1) {
        return `<svg width="18" height="18" viewBox="0 0 24 24" fill="none" stroke="#2563eb" stroke-width="2" style="margin-right:8px; vertical-align:middle;"><rect x="3" y="4" width="18" height="18" rx="2" ry="2"></rect><line x1="16" y1="2" x2="16" y2="6"></line><line x1="8" y1="2" x2="8" y2="6"></line><line x1="3" y1="10" x2="21" y2="10"></line><line x1="8" y1="14" x2="8.01" y2="14"></line><line x1="12" y1="14" x2="12.01" y2="14"></line><line x1="16" y1="14" x2="16.01" y2="14"></line><line x1="8" y1="18" x2="8.01" y2="18"></line><line x1="12" y1="18" x2="12.01" y2="18"></line><line x1="16" y1="18" x2="16.01" y2="18"></line></svg>`;
    } else if (t.indexOf('perc') !== -1) {
        return `<svg width="18" height="18" viewBox="0 0 24 24" fill="none" stroke="#ea580c" stroke-width="2" style="margin-right:8px; vertical-align:middle;"><path d="M12 22s8-4 8-10V5l-8-3-8 3v7c0 6 8 10 8 10z"></path></svg>`;
    } else if (t.indexOf('employee') !== -1) {
        return `<svg width="18" height="18" viewBox="0 0 24 24" fill="none" stroke="#2563eb" stroke-width="2" style="margin-right:8px; vertical-align:middle;"><path d="M20 21v-2a4 4 0 0 0-4-4H8a4 4 0 0 0-4 4v2"></path><circle cx="12" cy="7" r="4"></circle></svg>`;
    } else if (t.indexOf('cycle') !== -1) {
        return `<svg width="18" height="18" viewBox="0 0 24 24" fill="none" stroke="#059669" stroke-width="2" style="margin-right:8px; vertical-align:middle;"><rect x="3" y="4" width="18" height="18" rx="2" ry="2"></rect><line x1="16" y1="2" x2="16" y2="6"></line><line x1="8" y1="2" x2="8" y2="6"></line><line x1="3" y1="10" x2="21" y2="10"></line></svg>`;
    } else if (t.indexOf('plan') !== -1) {
        return `<svg width="18" height="18" viewBox="0 0 24 24" fill="none" stroke="#d97706" stroke-width="2" style="margin-right:8px; vertical-align:middle;"><path d="M14 2H6a2 2 0 0 0-2 2v16a2 2 0 0 0 2 2h12a2 2 0 0 0 2-2V8z"></path><polyline points="14 2 14 8 20 8"></polyline><line x1="16" y1="13" x2="8" y2="13"></line><line x1="16" y1="17" x2="8" y2="17"></line></svg>`;
    } else if (t.indexOf('supervisor') !== -1) {
        return `<svg width="18" height="18" viewBox="0 0 24 24" fill="none" stroke="#7c3aed" stroke-width="2" style="margin-right:8px; vertical-align:middle;"><path d="M17 21v-2a4 4 0 0 0-4-4H5a4 4 0 0 0-4 4v2"></path><circle cx="9" cy="7" r="4"></circle><path d="M23 21v-2a4 4 0 0 0-3-3.87"></path><path d="M16 3.13a4 4 0 0 1 0 7.75"></path></svg>`;
    } else if (t.indexOf('reviewer') !== -1) {
        return `<svg width="18" height="18" viewBox="0 0 24 24" fill="none" stroke="#e11d48" stroke-width="2" style="margin-right:8px; vertical-align:middle;"><path d="M22 11.08V12a10 10 0 1 1-5.93-9.14"></path><polyline points="22 4 12 14.01 9 11.01"></polyline></svg>`;
    } else if (t.indexOf('hr') !== -1 || t.indexOf('admin') !== -1) {
        return `<svg width="18" height="18" viewBox="0 0 24 24" fill="none" stroke="#0284c7" stroke-width="2" style="margin-right:8px; vertical-align:middle;"><path d="M12 22s8-4 8-10V5l-8-3-8 3v7c0 6 8 10 8 10z"></path></svg>`;
    } else if (t.indexOf('amendment') !== -1) {
        return `<svg width="18" height="18" viewBox="0 0 24 24" fill="none" stroke="#0d9488" stroke-width="2" style="margin-right:8px; vertical-align:middle;"><path d="M11 4H4a2 2 0 0 0-2 2v14a2 2 0 0 0 2 2h14a2 2 0 0 0 2-2v-7"></path><path d="M18.5 2.5a2.121 2.121 0 0 1 3 3L12 15l-4 1 1-4 9.5-9.5z"></path></svg>`;
    }
    return '';
};

window.pms_enhance_sidebar_items = function () {
    // Clean up any unwanted blue highlight or inline styles on sidebar items
    $('.sidebar-item-container, .standard-sidebar-item, .item-anchor, .sidebar-item-label').each(function () {
        var $el = $(this);
        var style = $el.attr('style') || '';
        if (style.indexOf('#eff6ff') !== -1 || style.indexOf('rgb(37, 99, 235)') !== -1 || style.indexOf('rgba(37') !== -1 || style.indexOf('box-shadow') !== -1) {
            $el.css({
                'background-color': '',
                'color': '',
                'font-weight': '',
                'border-radius': '',
                'box-shadow': ''
            });
            $el.removeClass('active selected');
        }
    });
};

window.pms_enhance_top_left_logo = function () {
    // 1. Sidebar Top Left Brand / Logo
    var $headers = $('.sidebar-header, .app-switcher, .workspace-sidebar-header, .app-sidebar-header, .desk-sidebar-header, .body-sidebar, .standard-sidebar-header');
    $headers.each(function () {
        var $h = $(this);
        var $avatar = $h.find('.avatar-frame, .avatar, .header-logo, .sidebar-image, .sidebar-brand-icon').first();
        if ($avatar.length && !$avatar.hasClass('pms-logo-processed')) {
            $avatar.addClass('pms-logo-processed').css({
                'background': 'transparent',
                'background-color': 'transparent',
                'border': 'none',
                'box-shadow': 'none'
            }).html('<img src="/assets/gdl_pms/logo_gdl.png" class="pms-top-logo" alt="GDL PMS Logo" style="height:32px; width:auto; max-width:38px; object-fit:contain; border-radius:6px; display:block;">');
        }
    });

    // 2. Top Navbar Brand Logo
    var $navBrand = $('.navbar-brand, .app-logo').first();
    if ($navBrand.length) {
        var $brandImg = $navBrand.find('img').first();
        if ($brandImg.length && $brandImg.attr('src') !== '/assets/gdl_pms/logo_gdl.png') {
            $brandImg.attr('src', '/assets/gdl_pms/logo_gdl.png');
        }
    }
};

// Run once on load to ensure clean sidebar state
if (window.pms_enhance_sidebar_items) window.pms_enhance_sidebar_items();

if (!window.pms_timer_started) {
    window.pms_timer_started = true;
    setInterval(function () {
        if (window.pms_enhance_top_left_logo) window.pms_enhance_top_left_logo();

        // Auto re-trigger workspace rendering if needed
        if (window.gdl_pms && gdl_pms.dashboard && gdl_pms.dashboard.check_and_render) {
            gdl_pms.dashboard.check_and_render();
        }
        if (window.gdl_pms && gdl_pms.supervisor_dashboard && gdl_pms.supervisor_dashboard.check_and_render) {
            gdl_pms.supervisor_dashboard.check_and_render();
        }
        if (window.gdl_pms && gdl_pms.reviewer_dashboard && gdl_pms.reviewer_dashboard.check_and_render) {
            gdl_pms.reviewer_dashboard.check_and_render();
        }
        if (window.gdl_pms && gdl_pms.hr_dashboard && gdl_pms.hr_dashboard.check_and_render) {
            gdl_pms.hr_dashboard.check_and_render();
        }
    }, 400);
}
