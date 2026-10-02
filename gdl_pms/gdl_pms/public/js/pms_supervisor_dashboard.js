frappe.provide('gdl_pms.supervisor_dashboard');

$(document).on('app_ready page-change workspace_rendered', function () {
    if (window.gdl_pms && gdl_pms.trigger_all_dashboards) {
        gdl_pms.trigger_all_dashboards();
    } else {
        gdl_pms.supervisor_dashboard.init();
    }
});

frappe.router.on('change', function () {
    if (window.gdl_pms && gdl_pms.trigger_all_dashboards) {
        gdl_pms.trigger_all_dashboards();
    } else {
        gdl_pms.supervisor_dashboard.schedule_checks();
    }
});

gdl_pms.supervisor_dashboard = {
    init: function () {
        this.schedule_checks();
    },

    schedule_checks: function () {
        if (window.gdl_pms && gdl_pms.trigger_all_dashboards) {
            gdl_pms.trigger_all_dashboards();
        } else {
            var self = this;
            self.check_and_render();
            [20, 80, 200, 500, 1000].forEach(function (delay) {
                setTimeout(function () {
                    self.check_and_render();
                }, delay);
            });
        }
    },

    is_supervisor_workspace: function () {
        var route = frappe.get_route() || [];
        if (!route.length) return false;
        var first = (route[0] || '').toLowerCase();
        if (['form', 'list', 'query-report', 'report', 'tree', 'print', 'modules', 'view'].indexOf(first) !== -1) {
            return false;
        }

        var full_route = (route || []).join('/').toLowerCase();
        var hash = (window.location.hash || '').toLowerCase();
        var pathname = (window.location.pathname || '').toLowerCase();
        var combined = full_route + ' ' + hash + ' ' + pathname;
        
        // Strictly exclude Supervisor 2 routes
        if (combined.indexOf('supervisor 2') !== -1 || combined.indexOf('supervisor-2') !== -1 || combined.indexOf('supervisor_2') !== -1 || full_route.indexOf('2') !== -1) {
            return false;
        }

        // Strictly exclude other roles
        if (full_route.indexOf('employee') !== -1 || full_route.indexOf('reviewer') !== -1 || full_route.indexOf('hr') !== -1 || full_route.indexOf('admin') !== -1) {
            return false;
        }

        return combined.indexOf('pms') !== -1 && combined.indexOf('supervisor') !== -1;
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
        if (!self.is_supervisor_workspace()) {
            $('[data-pms-dashboard="supervisor"]').remove();
            $('body, .layout-main-section, .workspace-page').removeClass('gdl-pms-supervisor-dashboard-active');
            return;
        }

        // We are on Supervisor Workspace: Purge any foreign PMS dashboards
        $('.gdl-pms-dashboard-wrapper:not([data-pms-dashboard="supervisor"]), .gdl-pms-supervisor-2-wrapper:not([data-pms-dashboard="supervisor"])').remove();

        $('body, .layout-main-section, .workspace-page')
            .removeClass('gdl-pms-employee-dashboard-active gdl-pms-reviewer-dashboard-active gdl-pms-supervisor-2-dashboard-active gdl-pms-hr-dashboard-active')
            .addClass('gdl-pms-custom-dashboard-active gdl-pms-supervisor-dashboard-active');

        var $container = self.get_container();
        if (!$container || !$container.length) return;

        if ($container.find('[data-pms-dashboard="supervisor"]').length > 0) {
            $container.children().not('[data-pms-dashboard="supervisor"]').hide();
            return;
        }

        self.render_dashboard($container);
    },

    render_dashboard: function ($container) {
        var self = this;
        if (!self.is_supervisor_workspace()) return;

        $container.children().not('[data-pms-dashboard="supervisor"]').hide();

        // Force parent containers to stretch 100% width
        $container.parents('.container, .page-body, .layout-main-section, .page-content, .layout-main-section-wrapper').css({
            'max-width': '100%',
            'width': '100%',
            'padding-left': '0',
            'padding-right': '0',
            'margin-left': '0',
            'margin-right': '0'
        });

        var $wrapper = $container.find('[data-pms-dashboard="supervisor"]');
        if (!$wrapper.length) {
            $wrapper = $(`
                <div class="gdl-pms-dashboard-wrapper" data-pms-dashboard="supervisor">
                    <div style="padding: 60px 20px; text-align: center; color: var(--text-muted);">
                        <div class="spinner-border text-primary" role="status" style="width: 2rem; height: 2rem;"></div>
                        <div style="margin-top: 12px; font-size: 14px; font-weight: 500;">Loading Supervisor Dashboard...</div>
                    </div>
                </div>
            `).appendTo($container);
        }

        frappe.call({
            method: 'gdl_pms.dashboard_api.get_supervisor_dashboard_data',
            callback: function (r) {
                if (!self.is_supervisor_workspace()) {
                    $('[data-pms-dashboard="supervisor"]').remove();
                    return;
                }
                if (r.message) {
                    var html = self.build_dashboard_html(r.message);
                    var $newWrapper = $(html);
                    $newWrapper.attr('data-pms-dashboard', 'supervisor');
                    if ($wrapper && $wrapper.parent().length) {
                        $wrapper.replaceWith($newWrapper);
                    } else {
                        $container.append($newWrapper);
                    }
                    $container.children().not('[data-pms-dashboard="supervisor"]').hide();
                    self.bind_events($container, r.message);
                }
            }
        });
    },

    build_dashboard_html: function (data) {
        var counts = data.counts || { pending_approvals: 0, team_plans: 0, approved_plans: 0 };
        var pending_items = data.pending_items || [];
        var cycles = data.cycles || [];

        var items_html = '';
        if (pending_items.length === 0) {
            items_html = `
                <div class="pms-empty-activity">
                    <p class="text-muted">No pending team approvals at this time. Great job!</p>
                </div>
            `;
        } else {
            pending_items.forEach(function (item) {
                items_html += `
                    <div class="pms-activity-row" data-doctype="${item.doctype}" data-name="${item.name}">
                        <div class="pms-activity-icon ${item.badge_class}">
                            <svg width="18" height="18" viewBox="0 0 24 24" fill="none" stroke="#d97706" stroke-width="2.5">
                                <circle cx="12" cy="12" r="10"></circle>
                                <polyline points="12 6 12 12 16 14"></polyline>
                            </svg>
                        </div>
                        <div class="pms-activity-details">
                            <div class="pms-activity-title">${frappe.utils.escape_html(item.title)}</div>
                            <div class="pms-activity-subtitle">${frappe.utils.escape_html(item.subtitle)}</div>
                        </div>
                        <div class="pms-activity-status">
                            <span class="pms-badge ${item.badge_class}">${frappe.utils.escape_html(item.status)}</span>
                        </div>
                    </div>
                `;
            });
        }

        var cycles_html = '';
        if (cycles.length === 0) {
            cycles_html = `
                <div class="pms-empty-activity">
                    <p class="text-muted">No active appraisal cycles found.</p>
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

        var cycle_options_html = '<option value="">Current Cycle</option>';
        cycles.forEach(function (c) {
            cycle_options_html += `<option value="${frappe.utils.escape_html(c.name)}">${frappe.utils.escape_html(c.cycle_name || c.name)}</option>`;
        });

        // return `
        // <div class="gdl-pms-dashboard-wrapper" data-pms-dashboard="supervisor">
        //     <!-- Top Greeting & Header Section -->
        //     <div class="pms-header-row">
        //         <div class="pms-greeting-col">
        //             <h1 class="pms-greeting-title">${frappe.utils.escape_html(data.greeting)} 👋</h1>
        //             <p class="pms-greeting-subtitle">Oversee and support your team's performance journey.</p>
        //         </div>
        //         <div class="pms-quote-col">
        //             <div class="pms-quote-text">"Leadership is about making others better as a result of your presence."</div>
        //             <div class="pms-quote-line"></div>
        //         </div>
        //     </div>

        //     <!-- Top 4 Stat Cards Row -->
        //     <div class="pms-stats-grid pms-stats-4col">
        //         <!-- Card 1: Pending Approvals -->
        //         <div class="pms-stat-card card-orange" data-action="pending-approvals">
        //             <div class="pms-stat-card-header">
        //                 <div class="pms-icon-box box-orange">
        //                     <svg width="22" height="22" viewBox="0 0 24 24" fill="none" stroke="#d97706" stroke-width="2">
        //                         <circle cx="12" cy="12" r="10"></circle>
        //                         <polyline points="12 6 12 12 16 14"></polyline>
        //                     </svg>
        //                 </div>
        //                 <div class="pms-stat-card-content">
        //                     <span class="pms-stat-title">Pending Approvals</span>
        //                     <span class="pms-stat-arrow-top">↗</span>
        //                 </div>
        //             </div>
        //             <div class="pms-stat-number-row">
        //                 <span class="pms-stat-number">${counts.pending_approvals}</span>
        //                 <button class="pms-circle-arrow-btn" aria-label="Review Pending">
        //                     <svg width="14" height="14" viewBox="0 0 24 24" fill="none" stroke="currentColor" stroke-width="2.5">
        //                         <path d="M9 18l6-6-6-6"/>
        //                     </svg>
        //                 </button>
        //             </div>
        //             <div class="pms-stat-subtext">Awaiting your review</div>
        //         </div>

        //         <!-- Card 2: Team Performance Plans -->
        //         <div class="pms-stat-card card-blue" data-action="team-plans">
        //             <div class="pms-stat-card-header">
        //                 <div class="pms-icon-box box-blue">
        //                     <svg width="22" height="22" viewBox="0 0 24 24" fill="none" stroke="#2563eb" stroke-width="2">
        //                         <path d="M17 21v-2a4 4 0 0 0-4-4H5a4 4 0 0 0-4 4v2"></path>
        //                         <circle cx="9" cy="7" r="4"></circle>
        //                         <path d="M23 21v-2a4 4 0 0 0-3-3.87"></path>
        //                         <path d="M16 3.13a4 4 0 0 1 0 7.75"></path>
        //                     </svg>
        //                 </div>
        //                 <div class="pms-stat-card-content">
        //                     <span class="pms-stat-title">Team Plans</span>
        //                     <span class="pms-stat-arrow-top">↗</span>
        //                 </div>
        //             </div>
        //             <div class="pms-stat-number-row">
        //                 <span class="pms-stat-number">${counts.team_plans}</span>
        //                 <button class="pms-circle-arrow-btn" aria-label="View Team Plans">
        //                     <svg width="14" height="14" viewBox="0 0 24 24" fill="none" stroke="currentColor" stroke-width="2.5">
        //                         <path d="M9 18l6-6-6-6"/>
        //                     </svg>
        //                 </button>
        //             </div>
        //             <div class="pms-stat-subtext">Total team plans</div>
        //         </div>

        //         <!-- Card 3: Active Cycles -->
        //         <div class="pms-stat-card card-teal" data-action="view-cycles">
        //             <div class="pms-stat-card-header">
        //                 <div class="pms-icon-box box-teal">
        //                     <svg width="20" height="20" viewBox="0 0 24 24" fill="none" stroke="#0d9488" stroke-width="2">
        //                         <circle cx="12" cy="12" r="10"></circle>
        //                         <polyline points="12 6 12 12 16 14"></polyline>
        //                     </svg>
        //                 </div>
        //                 <div class="pms-stat-card-content">
        //                     <span class="pms-stat-title">Active Cycles</span>
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
        //             <div class="pms-stat-subtext">Open appraisal periods</div>
        //         </div>

        //         <!-- Card 4: Approved Plans -->
        //         <div class="pms-stat-card card-green" data-action="approved-plans">
        //             <div class="pms-stat-card-header">
        //                 <div class="pms-icon-box box-green">
        //                     <svg width="22" height="22" viewBox="0 0 24 24" fill="none" stroke="#16a34a" stroke-width="2">
        //                         <path d="M22 11.08V12a10 10 0 1 1-5.93-9.14"></path>
        //                         <polyline points="22 4 12 14.01 9 11.01"></polyline>
        //                     </svg>
        //                 </div>
        //                 <div class="pms-stat-card-content">
        //                     <span class="pms-stat-title">Approved Plans</span>
        //                     <span class="pms-stat-arrow-top">↗</span>
        //                 </div>
        //             </div>
        //             <div class="pms-stat-number-row">
        //                 <span class="pms-stat-number">${counts.approved_plans}</span>
        //                 <button class="pms-circle-arrow-btn" aria-label="View Approved">
        //                     <svg width="14" height="14" viewBox="0 0 24 24" fill="none" stroke="currentColor" stroke-width="2.5">
        //                         <path d="M9 18l6-6-6-6"/>
        //                     </svg>
        //                 </button>
        //             </div>
        //             <div class="pms-stat-subtext">Successfully finalized</div>
        //         </div>
        //     </div>

        //     <!-- Middle Section: Quick Actions & Banner -->
        //     <div class="pms-mid-grid">
        //         <!-- Quick Actions Section -->
        //         <div class="pms-section-card pms-quick-actions-card">
        //             <div class="pms-section-header">
        //                 <span class="pms-section-icon">⚡</span>
        //                 <h2 class="pms-section-title">Supervisor Quick Actions</h2>
        //             </div>
        //             <div class="pms-quick-actions-grid">
        //                 <div class="pms-action-tile tile-orange" data-action="pending-approvals">
        //                     <div class="pms-action-icon-box">
        //                         <svg width="20" height="20" viewBox="0 0 24 24" fill="none" stroke="#ea580c" stroke-width="2">
        //                             <polyline points="9 11 12 14 22 4"></polyline>
        //                             <path d="M21 12v7a2 2 0 0 1-2 2H5a2 2 0 0 1-2-2V5a2 2 0 0 1 2-2h11"></path>
        //                         </svg>
        //                     </div>
        //                     <span class="pms-action-label">Review Team<br>Plans</span>
        //                 </div>

        //                 <div class="pms-action-tile tile-green" data-action="pending-amendments">
        //                     <div class="pms-action-icon-box">
        //                         <svg width="20" height="20" viewBox="0 0 24 24" fill="none" stroke="#16a34a" stroke-width="2">
        //                             <path d="M11 4H4a2 2 0 0 0-2 2v14a2 2 0 0 0 2 2h14a2 2 0 0 0 2-2v-7"></path>
        //                             <path d="M18.5 2.5a2.121 2.121 0 0 1 3 3L12 15l-4 1 1-4 9.5-9.5z"></path>
        //                         </svg>
        //                     </div>
        //                     <span class="pms-action-label">Review<br>Amendments</span>
        //                 </div>

        //                 <div class="pms-action-tile tile-blue" data-action="team-report">
        //                     <div class="pms-action-icon-box">
        //                         <svg width="20" height="20" viewBox="0 0 24 24" fill="none" stroke="#2563eb" stroke-width="2">
        //                             <line x1="18" y1="20" x2="18" y2="10"></line>
        //                             <line x1="12" y1="20" x2="12" y2="4"></line>
        //                             <line x1="6" y1="20" x2="6" y2="14"></line>
        //                         </svg>
        //                     </div>
        //                     <span class="pms-action-label">Team Performance<br>Report</span>
        //                 </div>

        //                 <div class="pms-action-tile tile-purple" data-action="view-cycles">
        //                     <div class="pms-action-icon-box">
        //                         <svg width="20" height="20" viewBox="0 0 24 24" fill="none" stroke="#9333ea" stroke-width="2">
        //                             <rect x="3" y="4" width="18" height="18" rx="2" ry="2"></rect>
        //                             <line x1="16" y1="2" x2="16" y2="6"></line>
        //                             <line x1="8" y1="2" x2="8" y2="6"></line>
        //                             <line x1="3" y1="10" x2="21" y2="10"></line>
        //                         </svg>
        //                     </div>
        //                     <span class="pms-action-label">Appraisal<br>Cycles</span>
        //                 </div>
        //             </div>
        //         </div>

        //         <!-- Team Empowerment Banner Card -->
        //         <div class="pms-banner-card pms-banner-supervisor">
        //             <div class="pms-banner-bg">
        //                 <svg class="pms-banner-illustration" viewBox="0 0 400 240" fill="none">
        //                     <circle cx="340" cy="80" r="50" fill="rgba(251, 191, 36, 0.2)"/>
        //                     <path d="M200 240 Q 280 180, 380 100 L400 240 Z" fill="rgba(245, 158, 11, 0.15)"/>
        //                 </svg>
        //             </div>
        //             <div class="pms-banner-content">
        //                 <div class="pms-banner-badge badge-supervisor-tag">
        //                     <span>🎯 Team Empowerment</span>
        //                 </div>
        //                 <h2 class="pms-banner-title">Guide. Support. Empower.</h2>
        //                 <p class="pms-banner-desc">Review team goals, provide timely feedback, and keep performance milestones on track.</p>
        //                 <button class="btn pms-btn-primary" data-action="pending-approvals">
        //                     Review Pending Plans &nbsp;→
        //                 </button>
        //             </div>
        //         </div>
        //     </div>

        //     <!-- Bottom Section: Active Cycles & Pending Actions -->
        //     <div class="pms-bottom-grid">
        //         <!-- Active Appraisal Cycles Card -->
        //         <div class="pms-section-card pms-activity-card">
        //             <div class="pms-card-header-flex">
        //                 <div class="pms-section-header">
        //                     <svg width="18" height="18" viewBox="0 0 24 24" fill="none" stroke="#475569" stroke-width="2">
        //                         <path d="M23 4v6h-6M1 20v-6h6"></path>
        //                         <path d="M3.51 9a9 9 0 0114.85-3.36L23 10M1 14l4.64 4.36A9 9 0 0020.49 15"></path>
        //                     </svg>
        //                     <h2 class="pms-section-title">Active Appraisal Cycles</h2>
        //                 </div>
        //                 <button class="btn btn-xs btn-default pms-btn-view-all" data-action="view-cycles">View All</button>
        //             </div>
        //             <div class="pms-activity-list">
        //                 ${cycles_html}
        //             </div>
        //         </div>

        //         <!-- Pending Team Actions Card -->
        //         <div class="pms-section-card pms-activity-card">
        //             <div class="pms-card-header-flex">
        //                 <div class="pms-section-header">
        //                     <span class="pms-section-icon">⏳</span>
        //                     <h2 class="pms-section-title">Pending Team Actions</h2>
        //                 </div>
        //                 <button class="btn btn-xs btn-default pms-btn-view-all" data-action="pending-approvals">View All</button>
        //             </div>
        //             <div class="pms-activity-list">
        //                 ${items_html}
        //             </div>
        //         </div>
        //     </div>
        // </div>
        // `;
        return `
        <div class="gdl-pms-dashboard-wrapper" data-pms-dashboard="supervisor">
            <!-- Top Header Section -->
            <div class="pms-header-row">
                <div class="pms-greeting-col">
                    <h1 class="pms-greeting-title">${frappe.utils.escape_html(data.greeting)}</h1>
                    <p class="pms-greeting-subtitle">Oversee and support your team's performance journey.</p>
                </div>
                <div class="pms-quote-col">
                    <div class="pms-quote-text">"Leadership is about making others better as a result of your presence."</div>
                    <div class="pms-quote-line"></div>
                </div>
            </div>

            <!-- Top 4 Stat Cards Row -->
            <div class="pms-stats-grid pms-stats-4col">
                <!-- Card 1: Pending Approvals -->
                <div class="pms-stat-card card-orange" data-action="pending-approvals">
                    <div class="pms-stat-card-header">
                        <div class="pms-icon-box box-orange">
                            <svg width="20" height="20" viewBox="0 0 24 24" fill="none" stroke="#d97706" stroke-width="2">
                                <circle cx="12" cy="12" r="10"></circle>
                                <polyline points="12 6 12 12 16 14"></polyline>
                            </svg>
                        </div>
                        <span class="pms-stat-title">Pending Approvals</span>
                    </div>
                    <div class="pms-stat-number-row">
                        <span class="pms-stat-number">${counts.pending_approvals}</span>
                        <button class="pms-circle-arrow-btn" aria-label="Review Pending">
                            <svg width="13" height="13" viewBox="0 0 24 24" fill="none" stroke="currentColor" stroke-width="2.5">
                                <path d="M9 18l6-6-6-6"/>
                            </svg>
                        </button>
                    </div>
                    <div class="pms-stat-subtext">Awaiting your review</div>
                </div>

                <!-- Card 2: Team Performance Plans -->
                <div class="pms-stat-card card-blue" data-action="team-plans">
                    <div class="pms-stat-card-header">
                        <div class="pms-icon-box box-blue">
                            <svg width="20" height="20" viewBox="0 0 24 24" fill="none" stroke="#2563eb" stroke-width="2">
                                <path d="M17 21v-2a4 4 0 0 0-4-4H5a4 4 0 0 0-4 4v2"></path>
                                <circle cx="9" cy="7" r="4"></circle>
                                <path d="M23 21v-2a4 4 0 0 0-3-3.87"></path>
                                <path d="M16 3.13a4 4 0 0 1 0 7.75"></path>
                            </svg>
                        </div>
                        <span class="pms-stat-title">Team Plans</span>
                    </div>
                    <div class="pms-stat-number-row">
                        <span class="pms-stat-number">${counts.team_plans}</span>
                        <button class="pms-circle-arrow-btn" aria-label="View Team Plans">
                            <svg width="13" height="13" viewBox="0 0 24 24" fill="none" stroke="currentColor" stroke-width="2.5">
                                <path d="M9 18l6-6-6-6"/>
                            </svg>
                        </button>
                    </div>
                    <div class="pms-stat-subtext">Total team plans</div>
                </div>

                <!-- Card 3: Active Cycles -->
                <div class="pms-stat-card card-teal" data-action="view-cycles">
                    <div class="pms-stat-card-header">
                        <div class="pms-icon-box box-teal">
                            <svg width="20" height="20" viewBox="0 0 24 24" fill="none" stroke="#0d9488" stroke-width="2">
                                <circle cx="12" cy="12" r="10"></circle>
                                <polyline points="12 6 12 12 16 14"></polyline>
                            </svg>
                        </div>
                        <span class="pms-stat-title">Active Cycles</span>
                    </div>
                    <div class="pms-stat-number-row">
                        <span class="pms-stat-number">${counts.active_cycles || 0}</span>
                        <button class="pms-circle-arrow-btn" aria-label="View Cycles">
                            <svg width="13" height="13" viewBox="0 0 24 24" fill="none" stroke="currentColor" stroke-width="2.5">
                                <path d="M9 18l6-6-6-6"/>
                            </svg>
                        </button>
                    </div>
                    <div class="pms-stat-subtext">Open appraisal periods</div>
                </div>

                <!-- Card 4: Approved Plans -->
                <div class="pms-stat-card card-green" data-action="approved-plans">
                    <div class="pms-stat-card-header">
                        <div class="pms-icon-box box-green">
                            <svg width="20" height="20" viewBox="0 0 24 24" fill="none" stroke="#16a34a" stroke-width="2">
                                <path d="M22 11.08V12a10 10 0 1 1-5.93-9.14"></path>
                                <polyline points="22 4 12 14.01 9 11.01"></polyline>
                            </svg>
                        </div>
                        <span class="pms-stat-title">Approved Plans</span>
                    </div>
                    <div class="pms-stat-number-row">
                        <span class="pms-stat-number">${counts.approved_plans}</span>
                        <button class="pms-circle-arrow-btn" aria-label="View Approved">
                            <svg width="13" height="13" viewBox="0 0 24 24" fill="none" stroke="currentColor" stroke-width="2.5">
                                <path d="M9 18l6-6-6-6"/>
                            </svg>
                        </button>
                    </div>
                    <div class="pms-stat-subtext">Successfully finalized</div>
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
                        <h2 class="pms-section-title">Supervisor Quick Actions</h2>
                    </div>
                    <div class="pms-quick-actions-grid">
                        <div class="pms-action-tile tile-orange" data-action="pending-approvals">
                            <div class="pms-action-icon-box">
                                <svg width="18" height="18" viewBox="0 0 24 24" fill="none" stroke="#ea580c" stroke-width="2">
                                    <polyline points="9 11 12 14 22 4"></polyline>
                                    <path d="M21 12v7a2 2 0 0 1-2 2H5a2 2 0 0 1-2-2V5a2 2 0 0 1 2-2h11"></path>
                                </svg>
                            </div>
                            <span class="pms-action-label">Review Team Plans</span>
                        </div>

                        <div class="pms-action-tile tile-green" data-action="pending-amendments">
                            <div class="pms-action-icon-box">
                                <svg width="18" height="18" viewBox="0 0 24 24" fill="none" stroke="#16a34a" stroke-width="2">
                                    <path d="M11 4H4a2 2 0 0 0-2 2v14a2 2 0 0 0 2 2h14a2 2 0 0 0 2-2v-7"></path>
                                    <path d="M18.5 2.5a2.121 2.121 0 0 1 3 3L12 15l-4 1 1-4 9.5-9.5z"></path>
                                </svg>
                            </div>
                            <span class="pms-action-label">Review Amendments</span>
                        </div>

                        <div class="pms-action-tile tile-blue" data-action="team-report">
                            <div class="pms-action-icon-box">
                                <svg width="18" height="18" viewBox="0 0 24 24" fill="none" stroke="#2563eb" stroke-width="2">
                                    <line x1="18" y1="20" x2="18" y2="10"></line>
                                    <line x1="12" y1="20" x2="12" y2="4"></line>
                                    <line x1="6" y1="20" x2="6" y2="14"></line>
                                </svg>
                            </div>
                            <span class="pms-action-label">Team Performance Report</span>
                        </div>

                        <div class="pms-action-tile tile-purple" data-action="view-cycles">
                            <div class="pms-action-icon-box">
                                <svg width="18" height="18" viewBox="0 0 24 24" fill="none" stroke="#9333ea" stroke-width="2">
                                    <rect x="3" y="4" width="18" height="18" rx="2" ry="2"></rect>
                                    <line x1="16" y1="2" x2="16" y2="6"></line>
                                    <line x1="8" y1="2" x2="8" y2="6"></line>
                                    <line x1="3" y1="10" x2="21" y2="10"></line>
                                </svg>
                            </div>
                            <span class="pms-action-label">Appraisal Cycles</span>
                        </div>
                    </div>
                </div>

                <!-- Team Empowerment Banner Card -->
                <div class="pms-banner-card pms-banner-supervisor">
                    <div class="pms-banner-bg">
                        <svg class="pms-banner-illustration" viewBox="0 0 400 240" fill="none">
                            <circle cx="340" cy="80" r="50" fill="rgba(251, 191, 36, 0.2)"/>
                            <path d="M200 240 Q 280 180, 380 100 L400 240 Z" fill="rgba(245, 158, 11, 0.15)"/>
                        </svg>
                    </div>
                    <div class="pms-banner-content">
                        <div class="pms-banner-badge badge-supervisor-tag">
                            <svg width="14" height="14" viewBox="0 0 24 24" fill="none" stroke="#d97706" stroke-width="2">
                                <circle cx="12" cy="12" r="10"></circle>
                                <circle cx="12" cy="12" r="6"></circle>
                                <circle cx="12" cy="12" r="2"></circle>
                            </svg>
                            <span>Team Empowerment</span>
                        </div>
                        <h2 class="pms-banner-title">Guide. Support. Empower.</h2>
                        <p class="pms-banner-desc">Review team goals, provide timely feedback, and keep performance milestones on track.</p>
                        <button class="btn pms-btn-primary" data-action="pending-approvals">
                            Review Pending Plans
                            <svg width="14" height="14" viewBox="0 0 24 24" fill="none" stroke="currentColor" stroke-width="2.5">
                                <path d="M5 12h14M13 6l6 6-6 6"/>
                            </svg>
                        </button>
                    </div>
                </div>
            </div>

            <!-- Bottom Section: Active Cycles & Pending Actions -->
            <div class="pms-bottom-grid">
                <!-- Active Appraisal Cycles Card -->
                <div class="pms-section-card pms-activity-card">
                    <div class="pms-card-header-flex">
                        <div class="pms-section-header">
                            <svg width="18" height="18" viewBox="0 0 24 24" fill="none" stroke="#475569" stroke-width="2">
                                <path d="M23 4v6h-6M1 20v-6h6"></path>
                                <path d="M3.51 9a9 9 0 0114.85-3.36L23 10M1 14l4.64 4.36A9 9 0 0020.49 15"></path>
                            </svg>
                            <h2 class="pms-section-title">Active Appraisal Cycles</h2>
                        </div>
                        <button class="btn btn-xs btn-default pms-btn-view-all" data-action="view-cycles">View All</button>
                    </div>
                    <div class="pms-activity-list">
                        ${cycles_html}
                    </div>
                </div>

                <!-- Pending Team Actions Card -->
                <div class="pms-section-card pms-activity-card">
                    <div class="pms-card-header-flex">
                        <div class="pms-section-header">
                            <svg width="18" height="18" viewBox="0 0 24 24" fill="none" stroke="#475569" stroke-width="2">
                                <circle cx="12" cy="12" r="10"></circle>
                                <polyline points="12 8 12 12 15 15"></polyline>
                            </svg>
                            <h2 class="pms-section-title">Pending Team Actions</h2>
                        </div>
                        <button class="btn btn-xs btn-default pms-btn-view-all" data-action="pending-approvals">View All</button>
                    </div>
                    <div class="pms-activity-list">
                        ${items_html}
                    </div>
                </div>
            </div>
        </div>
        `;  
    },

    bind_events: function ($container) {
        $container.find('[data-action]').on('click', function (e) {
            e.stopPropagation();
            var action = $(this).data('action');

            if (action === 'pending-approvals') {
                frappe.set_route('List', 'PMS Appraisal', { plan_status: 'Pending Supervisor Approval' });
            } else if (action === 'pending-amendments') {
                frappe.set_route('List', 'PMS Plan Amendment', { status: 'Pending Supervisor Approval' });
            } else if (action === 'team-plans') {
                frappe.set_route('List', 'PMS Appraisal');
            } else if (action === 'approved-plans') {
                frappe.set_route('List', 'PMS Appraisal', { plan_status: 'Approved' });
            } else if (action === 'team-report') {
                frappe.set_route('query-report', 'PMS Office Report');
            } else if (action === 'view-cycles') {
                frappe.set_route('List', 'PMS Appraisal Cycle');
            } else if (action === 'route-cycle') {
                var cycleName = $(this).data('name');
                if (cycleName) {
                    frappe.set_route('Form', 'PMS Appraisal Cycle', cycleName);
                } else {
                    frappe.set_route('List', 'PMS Appraisal Cycle');
                }
            }
        });

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
