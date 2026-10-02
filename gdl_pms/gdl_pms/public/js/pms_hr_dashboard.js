frappe.provide('gdl_pms.hr_dashboard');

$(document).on('app_ready page-change workspace_rendered', function () {
    if (window.gdl_pms && gdl_pms.trigger_all_dashboards) {
        gdl_pms.trigger_all_dashboards();
    } else {
        gdl_pms.hr_dashboard.init();
    }
});

frappe.router.on('change', function () {
    if (window.gdl_pms && gdl_pms.trigger_all_dashboards) {
        gdl_pms.trigger_all_dashboards();
    } else {
        gdl_pms.hr_dashboard.schedule_checks();
    }
});

gdl_pms.hr_dashboard = {
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

    is_hr_workspace: function () {
        var route = frappe.get_route() || [];
        if (!route.length) return false;
        var first = (route[0] || '').toLowerCase();
        if (['form', 'list', 'query-report', 'report', 'tree', 'print', 'modules', 'view'].indexOf(first) !== -1) {
            return false;
        }

        var full_route = (route || []).join('/').toLowerCase();
        if (full_route.indexOf('supervisor') !== -1 || full_route.indexOf('employee') !== -1 || full_route.indexOf('reviewer') !== -1) {
            return false;
        }

        var hash = (window.location.hash || '').toLowerCase();
        var pathname = (window.location.pathname || '').toLowerCase();
        var combined = full_route + ' ' + hash + ' ' + pathname;

        return combined.indexOf('pms') !== -1 && (combined.indexOf('hr') !== -1 || combined.indexOf('admin') !== -1);
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
        if (!self.is_hr_workspace()) {
            $('[data-pms-dashboard="hr"]').remove();
            $('body, .layout-main-section, .workspace-page').removeClass('gdl-pms-hr-dashboard-active');
            return;
        }

        // We are on HR Workspace: Purge any foreign PMS dashboards
        $('.gdl-pms-dashboard-wrapper:not([data-pms-dashboard="hr"]), .gdl-pms-supervisor-2-wrapper:not([data-pms-dashboard="hr"])').remove();

        $('body, .layout-main-section, .workspace-page')
            .removeClass('gdl-pms-employee-dashboard-active gdl-pms-supervisor-dashboard-active gdl-pms-reviewer-dashboard-active gdl-pms-supervisor-2-dashboard-active')
            .addClass('gdl-pms-custom-dashboard-active gdl-pms-hr-dashboard-active');

        var $container = self.get_container();
        if (!$container || !$container.length) return;

        if ($container.find('[data-pms-dashboard="hr"]').length > 0) {
            $container.children().not('[data-pms-dashboard="hr"]').hide();
            return;
        }

        self.render_dashboard($container);
    },

    render_dashboard: function ($container) {
        var self = this;
        if (!self.is_hr_workspace()) return;

        $container.children().not('[data-pms-dashboard="hr"]').hide();

        // Force parent containers to stretch 100% width
        $container.parents('.container, .page-body, .layout-main-section, .page-content, .layout-main-section-wrapper').css({
            'max-width': '100%',
            'width': '100%',
            'padding-left': '0',
            'padding-right': '0',
            'margin-left': '0',
            'margin-right': '0'
        });

        var $wrapper = $container.find('[data-pms-dashboard="hr"]');
        if (!$wrapper.length) {
            $wrapper = $(`
                <div class="gdl-pms-dashboard-wrapper" data-pms-dashboard="hr">
                    <div style="padding: 60px 20px; text-align: center; color: var(--text-muted);">
                        <div class="spinner-border text-primary" role="status" style="width: 2rem; height: 2rem;"></div>
                        <div style="margin-top: 12px; font-size: 14px; font-weight: 500;">Loading HR Admin Dashboard...</div>
                    </div>
                </div>
            `).appendTo($container);
        }

        frappe.call({
            method: 'gdl_pms.dashboard_api.get_hr_dashboard_data',
            callback: function (r) {
                if (!self.is_hr_workspace()) {
                    $('[data-pms-dashboard="hr"]').remove();
                    return;
                }
                if (r.message) {
                    var html = self.build_dashboard_html(r.message);
                    var $newWrapper = $(html);
                    $newWrapper.attr('data-pms-dashboard', 'hr');
                    if ($wrapper && $wrapper.parent().length) {
                        $wrapper.replaceWith($newWrapper);
                    } else {
                        $container.append($newWrapper);
                    }
                    $container.children().not('[data-pms-dashboard="hr"]').hide();
                    self.bind_events($container, r.message);
                }
            }
        });
    },

    build_dashboard_html: function (data) {
        var counts = data.counts || { active_employees: 0, total_appraisals: 0, active_cycles: 0, pending_perc: 0 };
        var cycles = data.cycles || [];
        var perc_cases = data.perc_cases || [];

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
                    <div class="pms-activity-row" data-action="route-cycle" data-name="${c.name}">
                        <div class="pms-activity-icon ${c.badge_class}">
                            <svg width="18" height="18" viewBox="0 0 24 24" fill="none" stroke="#16a34a" stroke-width="2.5">
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

               return `
        <div class="gdl-pms-dashboard-wrapper" data-pms-dashboard="hr">
            <!-- Top Header Section -->
            <div class="pms-header-row">
                <div class="pms-greeting-col">
                    <h1 class="pms-greeting-title">${frappe.utils.escape_html(data.greeting)}</h1>
                    <p class="pms-greeting-subtitle">Overview of organization performance cycles, compliance, and PERC cases.</p>
                </div>
                <div class="pms-quote-col">
                    <div class="pms-quote-text">"Human resources isn't a thing we do. It's the thing that runs our business."</div>
                    <div class="pms-quote-line"></div>
                </div>
            </div>

            <!-- Top 4 Stat Cards Row -->
            <div class="pms-stats-grid pms-stats-4col">
                <!-- Card 1: Active Employees -->
                <div class="pms-stat-card card-blue" data-action="route-employees">
                    <div class="pms-stat-card-header">
                        <div class="pms-icon-box box-blue">
                            <svg width="20" height="20" viewBox="0 0 24 24" fill="none" stroke="#2563eb" stroke-width="2">
                                <path d="M17 21v-2a4 4 0 0 0-4-4H5a4 4 0 0 0-4 4v2"></path>
                                <circle cx="9" cy="7" r="4"></circle>
                                <path d="M23 21v-2a4 4 0 0 0-3-3.87"></path>
                                <path d="M16 3.13a4 4 0 0 1 0 7.75"></path>
                            </svg>
                        </div>
                        <span class="pms-stat-title">Active Employees</span>
                    </div>
                    <div class="pms-stat-number-row">
                        <span class="pms-stat-number">${counts.active_employees}</span>
                        <button class="pms-circle-arrow-btn" aria-label="View Employees">
                            <svg width="13" height="13" viewBox="0 0 24 24" fill="none" stroke="currentColor" stroke-width="2.5">
                                <path d="M9 18l6-6-6-6"/>
                            </svg>
                        </button>
                    </div>
                    <div class="pms-stat-subtext">Active workforce</div>
                </div>

                <!-- Card 2: Total Appraisals -->
                <div class="pms-stat-card card-purple" data-action="route-appraisals">
                    <div class="pms-stat-card-header">
                        <div class="pms-icon-box box-purple">
                            <svg width="20" height="20" viewBox="0 0 24 24" fill="none" stroke="#9333ea" stroke-width="2">
                                <path d="M14 2H6a2 2 0 0 0-2 2v16a2 2 0 0 0 2 2h12a2 2 0 0 0 2-2V8z"></path>
                                <polyline points="14 2 14 8 20 8"></polyline>
                            </svg>
                        </div>
                        <span class="pms-stat-title">Total Appraisals</span>
                    </div>
                    <div class="pms-stat-number-row">
                        <span class="pms-stat-number">${counts.total_appraisals}</span>
                        <button class="pms-circle-arrow-btn" aria-label="View Appraisals">
                            <svg width="13" height="13" viewBox="0 0 24 24" fill="none" stroke="currentColor" stroke-width="2.5">
                                <path d="M9 18l6-6-6-6"/>
                            </svg>
                        </button>
                    </div>
                    <div class="pms-stat-subtext">Organization-wide plans</div>
                </div>

                <!-- Card 3: Active Cycles -->
                <div class="pms-stat-card card-green" data-action="route-cycles">
                    <div class="pms-stat-card-header">
                        <div class="pms-icon-box box-green">
                            <svg width="20" height="20" viewBox="0 0 24 24" fill="none" stroke="#16a34a" stroke-width="2">
                                <circle cx="12" cy="12" r="10"></circle>
                                <polyline points="12 6 12 12 16 14"></polyline>
                            </svg>
                        </div>
                        <span class="pms-stat-title">Active Cycles</span>
                    </div>
                    <div class="pms-stat-number-row">
                        <span class="pms-stat-number">${counts.active_cycles}</span>
                        <button class="pms-circle-arrow-btn" aria-label="View Cycles">
                            <svg width="13" height="13" viewBox="0 0 24 24" fill="none" stroke="currentColor" stroke-width="2.5">
                                <path d="M9 18l6-6-6-6"/>
                            </svg>
                        </button>
                    </div>
                    <div class="pms-stat-subtext">Current performance cycles</div>
                </div>

                <!-- Card 4: Pending PERC Cases -->
                <div class="pms-stat-card card-orange" data-action="route-perc">
                    <div class="pms-stat-card-header">
                        <div class="pms-icon-box box-orange">
                            <svg width="20" height="20" viewBox="0 0 24 24" fill="none" stroke="#ea580c" stroke-width="2">
                                <path d="M10.29 3.86L1.82 18a2 2 0 0 0 1.71 3h16.94a2 2 0 0 0 1.71-3L13.71 3.86a2 2 0 0 0-3.42 0z"></path>
                                <line x1="12" y1="9" x2="12" y2="13"></line>
                                <line x1="12" y1="17" x2="12.01" y2="17"></line>
                            </svg>
                        </div>
                        <span class="pms-stat-title">Pending PERC</span>
                    </div>
                    <div class="pms-stat-number-row">
                        <span class="pms-stat-number">${counts.pending_perc}</span>
                        <button class="pms-circle-arrow-btn" aria-label="View PERC">
                            <svg width="13" height="13" viewBox="0 0 24 24" fill="none" stroke="currentColor" stroke-width="2.5">
                                <path d="M9 18l6-6-6-6"/>
                            </svg>
                        </button>
                    </div>
                    <div class="pms-stat-subtext">Dispute cases open</div>
                </div>
            </div>

            <!-- Middle Section: Quick Actions & Banner -->
            <div class="pms-mid-grid">
                <!-- Quick Actions Section -->
                <div class="pms-section-card pms-quick-actions-card">
                    <div class="pms-section-header">
                        <svg width="18" height="18" viewBox="0 0 24 24" fill="none" stroke="#475569" stroke-width="2">
                            <path d="M13 2L3 14h7l-1 8 10-12h-7l1-8z"></path>
                        </svg>
                        <h2 class="pms-section-title">HR Admin Actions</h2>
                    </div>
                    <div class="pms-quick-actions-grid">
                        <div class="pms-action-tile tile-teal" data-action="new-employee">
                            <div class="pms-action-icon-box">
                                <svg width="18" height="18" viewBox="0 0 24 24" fill="none" stroke="#0d9488" stroke-width="2">
                                    <path d="M16 21v-2a4 4 0 0 0-4-4H5a4 4 0 0 0-4 4v2"></path>
                                    <circle cx="8.5" cy="7" r="4"></circle>
                                    <line x1="20" y1="8" x2="20" y2="14"></line>
                                    <line x1="17" y1="11" x2="23" y2="11"></line>
                                </svg>
                            </div>
                            <span class="pms-action-label">Add New Employee</span>
                        </div>

                        <div class="pms-action-tile tile-green" data-action="new-cycle">
                            <div class="pms-action-icon-box">
                                <svg width="18" height="18" viewBox="0 0 24 24" fill="none" stroke="#16a34a" stroke-width="2">
                                    <line x1="12" y1="5" x2="12" y2="19"></line>
                                    <line x1="5" y1="12" x2="19" y2="12"></line>
                                </svg>
                            </div>
                            <span class="pms-action-label">Setup New Cycle</span>
                        </div>

                        <div class="pms-action-tile tile-teal" data-action="route-calendar">
                            <div class="pms-action-icon-box">
                                <svg width="18" height="18" viewBox="0 0 24 24" fill="none" stroke="#0d9488" stroke-width="2">
                                    <rect x="3" y="4" width="18" height="18" rx="2" ry="2"></rect>
                                    <line x1="16" y1="2" x2="16" y2="6"></line>
                                    <line x1="8" y1="2" x2="8" y2="6"></line>
                                    <line x1="3" y1="10" x2="21" y2="10"></line>
                                </svg>
                            </div>
                            <span class="pms-action-label">PMS Calendar</span>
                        </div>

                        <div class="pms-action-tile tile-blue" data-action="route-appraisals">
                            <div class="pms-action-icon-box">
                                <svg width="18" height="18" viewBox="0 0 24 24" fill="none" stroke="#2563eb" stroke-width="2">
                                    <path d="M14 2H6a2 2 0 0 0-2 2v16a2 2 0 0 0 2 2h12a2 2 0 0 0 2-2V8z"></path>
                                </svg>
                            </div>
                            <span class="pms-action-label">All Performance Plans</span>
                        </div>

                        <div class="pms-action-tile tile-orange" data-action="route-perc">
                            <div class="pms-action-icon-box">
                                <svg width="18" height="18" viewBox="0 0 24 24" fill="none" stroke="#ea580c" stroke-width="2">
                                    <path d="M12 22s8-4 8-10V5l-8-3-8 3v7c0 6 8 10 8 10z"></path>
                                </svg>
                            </div>
                            <span class="pms-action-label">PERC Cases List</span>
                        </div>

                        <div class="pms-action-tile tile-purple" data-action="route-dept-report">
                            <div class="pms-action-icon-box">
                                <svg width="18" height="18" viewBox="0 0 24 24" fill="none" stroke="#9333ea" stroke-width="2">
                                    <line x1="18" y1="20" x2="18" y2="10"></line>
                                    <line x1="12" y1="20" x2="12" y2="4"></line>
                                    <line x1="6" y1="20" x2="6" y2="14"></line>
                                </svg>
                            </div>
                            <span class="pms-action-label">Office Reports</span>
                        </div>
                    </div>
                </div>

                <!-- HR Governance Banner Card -->
                <div class="pms-banner-card pms-banner-hr">
                    <div class="pms-banner-bg">
                        <svg class="pms-banner-illustration" viewBox="0 0 400 240" fill="none">
                            <circle cx="340" cy="80" r="50" fill="rgba(16, 185, 129, 0.15)"/>
                            <path d="M200 240 Q 280 180, 380 100 L400 240 Z" fill="rgba(5, 150, 105, 0.12)"/>
                        </svg>
                    </div>
                    <div class="pms-banner-content">
                        <div class="pms-banner-badge badge-hr-tag">
                            <svg width="14" height="14" viewBox="0 0 24 24" fill="none" stroke="#0d9488" stroke-width="2">
                                <path d="M3 21h18M5 21V7l7-4 7 4v14M9 9h1m4 0h1m-6 4h1m4 0h1m-6 4h1m4 0h1"></path>
                            </svg>
                            <span>HR Governance & Excellence</span>
                        </div>
                        <h2 class="pms-banner-title">Drive Growth. Ensure Equity.</h2>
                        <p class="pms-banner-desc">Monitor organization performance health, active cycles, and manage PERC resolutions seamlessly.</p>
                        <button class="btn pms-btn-primary btn-hr-banner" data-action="route-cycles">
                            Manage Appraisal Cycles
                            <svg width="14" height="14" viewBox="0 0 24 24" fill="none" stroke="currentColor" stroke-width="2.5">
                                <path d="M5 12h14M13 6l6 6-6 6"/>
                            </svg>
                        </button>
                    </div>
                </div>
            </div>

            <!-- Bottom Section: Active Cycles & Analytics -->
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
                        <button class="btn btn-xs btn-default pms-btn-view-all" data-action="route-cycles">View All</button>
                    </div>
                    <div class="pms-activity-list">
                        ${cycles_html}
                    </div>
                </div>

                <!-- Organization Completion Report Card -->
                <div class="pms-section-card pms-journey-card">
                    <div class="pms-card-header-flex">
                        <div class="pms-section-header">
                            <svg width="18" height="18" viewBox="0 0 24 24" fill="none" stroke="#475569" stroke-width="2">
                                <polyline points="22 12 18 12 15 21 9 3 6 12 2 12"></polyline>
                            </svg>
                            <h2 class="pms-section-title">Organization Completion & Analytics</h2>
                        </div>
                    </div>

                    <div class="pms-journey-empty-state">
                        <div class="pms-journey-icon-circle box-green">
                            <svg width="22" height="22" viewBox="0 0 24 24" fill="none" stroke="#16a34a" stroke-width="2">
                                <polyline points="22 12 18 12 15 21 9 3 6 12 2 12"></polyline>
                            </svg>
                        </div>
                        <h3 class="pms-journey-empty-title">PMS Analytics Suite</h3>
                        <p class="pms-journey-empty-desc">Generate completion reports, score analysis, and office performance breakdowns.</p>
                        <button class="btn pms-btn-outline" data-action="route-completion-report">Open Completion Report</button>
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

            if (action === 'new-employee') {
                frappe.new_doc('Employee');
            } else if (action === 'new-cycle') {
                frappe.new_doc('PMS Appraisal Cycle');
            } else if (action === 'route-cycles') {
                frappe.set_route('List', 'PMS Appraisal Cycle');
            } else if (action === 'route-appraisals') {
                frappe.set_route('List', 'PMS Appraisal');
            } else if (action === 'route-employees') {
                frappe.set_route('List', 'Employee');
            } else if (action === 'route-perc') {
                frappe.set_route('List', 'PERC Case');
            } else if (action === 'route-dept-report') {
                frappe.set_route('query-report', 'PMS Office Report');
            } else if (action === 'route-completion-report') {
                frappe.set_route('query-report', 'PMS Completion Report');
            } else if (action === 'route-calendar') {
                frappe.set_route('List', 'PMS Calendar');
            }
        });

        $container.find('.pms-activity-row').on('click', function () {
            var name = $(this).data('name');
            if (name) {
                frappe.set_route('Form', 'PMS Appraisal Cycle', name);
            }
        });
    }
};
