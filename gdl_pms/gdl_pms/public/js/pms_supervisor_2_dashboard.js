frappe.provide('gdl_pms.supervisor_2_dashboard');

$(document).on('app_ready page-change workspace_rendered', function () {
    if (window.gdl_pms && gdl_pms.trigger_all_dashboards) {
        gdl_pms.trigger_all_dashboards();
    } else {
        gdl_pms.supervisor_2_dashboard.init();
    }
});

frappe.router.on('change', function () {
    if (window.gdl_pms && gdl_pms.trigger_all_dashboards) {
        gdl_pms.trigger_all_dashboards();
    } else {
        gdl_pms.supervisor_2_dashboard.schedule_checks();
    }
});

gdl_pms.supervisor_2_dashboard = {
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

    is_supervisor_2_workspace: function () {
        var route = frappe.get_route() || [];
        if (!route.length) return false;

        var first = (route[0] || '').toLowerCase();
        if (['form', 'list', 'query-report', 'report', 'tree', 'print', 'modules', 'view'].indexOf(first) !== -1) {
            return false;
        }

        var full_route = route.join('/').toLowerCase();
        var hash = (window.location.hash || '').toLowerCase();
        var pathname = (window.location.pathname || '').toLowerCase();
        var combined = full_route + ' ' + hash + ' ' + pathname;

        return (
            combined.indexOf('supervisor') !== -1 &&
            (combined.indexOf('2') !== -1 || combined.indexOf('-2') !== -1) &&
            combined.indexOf('appraisal') === -1
        );
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
        if (!self.is_supervisor_2_workspace()) {
            $('[data-pms-dashboard="supervisor-2"]').remove();
            $('body, .layout-main-section, .workspace-page').removeClass('gdl-pms-supervisor-2-dashboard-active');
            return;
        }

        // We are on Supervisor 2 Workspace: Purge any foreign PMS dashboards
        $('.gdl-pms-dashboard-wrapper:not([data-pms-dashboard="supervisor-2"]), .gdl-pms-supervisor-2-wrapper:not([data-pms-dashboard="supervisor-2"])').remove();

        $('body, .layout-main-section, .workspace-page')
            .removeClass('gdl-pms-employee-dashboard-active gdl-pms-supervisor-dashboard-active gdl-pms-reviewer-dashboard-active gdl-pms-hr-dashboard-active')
            .addClass('gdl-pms-custom-dashboard-active gdl-pms-supervisor-2-dashboard-active');

        var $container = self.get_container();
        if (!$container || !$container.length) return;

        if ($container.find('[data-pms-dashboard="supervisor-2"]').length > 0) {
            $container.children().not('[data-pms-dashboard="supervisor-2"]').hide();
            return;
        }

        self.render_dashboard($container);
    },

    render_dashboard: function ($container) {
        var self = this;
        if (!self.is_supervisor_2_workspace()) return;

        $container.children().not('[data-pms-dashboard="supervisor-2"]').hide();

        $container.parents('.container, .page-body, .page-content, .layout-main-section-wrapper').css({
            'max-width': '100%',
            'width': '100%',
            'padding-left': '0',
            'padding-right': '0',
            'margin-left': '0',
            'margin-right': '0'
        });

        var $wrapper = $container.find('[data-pms-dashboard="supervisor-2"]');
        if (!$wrapper.length) {
            $wrapper = $(`
                <div class="gdl-pms-supervisor-2-wrapper gdl-pms-dashboard-wrapper" data-pms-dashboard="supervisor-2">
                    <div style="padding: 60px 20px; text-align: center; color: var(--text-muted);">
                        <div class="spinner-border text-primary" role="status" style="width: 2rem; height: 2rem;"></div>
                        <div style="margin-top: 12px; font-size: 14px; font-weight: 500;">Loading Supervisor 2 Dashboard...</div>
                    </div>
                </div>
            `).appendTo($container);
        }

        frappe.call({
            method: 'gdl_pms.dashboard_api.get_supervisor_2_dashboard_data',
            callback: function (r) {
                if (!self.is_supervisor_2_workspace()) {
                    $('[data-pms-dashboard="supervisor-2"]').remove();
                    return;
                }
                if (r.message) {
                    var html = self.build_dashboard_html(r.message);
                    var $newWrapper = $(html);
                    $newWrapper.attr('data-pms-dashboard', 'supervisor-2');
                    if ($wrapper && $wrapper.parent().length) {
                        $wrapper.replaceWith($newWrapper);
                    } else {
                        $container.append($newWrapper);
                    }
                    $container.children().not('[data-pms-dashboard="supervisor-2"]').hide();
                    self.bind_events($container, r.message);
                }
            }
        });
    },

    build_dashboard_html: function (data) {
        var counts = data.counts || { total_monitored: 0, approved: 0, pending: 0, draft: 0 };
        var plans = data.plans || [];

        var rows_html = '';
        if (plans.length === 0) {
            rows_html = `
                <tr>
                    <td colspan="6" class="text-center text-muted" style="padding: 32px 16px;">
                        <div style="font-size: 14px; font-weight: 500;">No employees are currently assigned to you as Supervisor 2.</div>
                        <div style="font-size: 12px; margin-top: 4px;">Assigned employee performance plans will automatically appear here for monitoring.</div>
                    </td>
                </tr>
            `;
        } else {
            plans.forEach(function (plan) {
                rows_html += `
                    <tr class="pms-monitoring-row" data-name="${frappe.utils.escape_html(plan.name)}" style="cursor: pointer; transition: background-color 0.15s ease;">
                        <td style="padding: 14px 16px;">
                            <div style="font-weight: 600; color: var(--text-color); font-size: 13.5px;">${frappe.utils.escape_html(plan.employee_name)}</div>
                            <div style="font-size: 11.5px; color: var(--text-muted);">${frappe.utils.escape_html(plan.employee_id)} &bull; ${frappe.utils.escape_html(plan.department)}</div>
                        </td>
                        <td style="padding: 14px 16px; font-size: 13px; color: var(--text-color);">
                            ${frappe.utils.escape_html(plan.cycle)}
                        </td>
                        <td style="padding: 14px 16px; font-size: 13px;">
                            <span class="badge" style="background: rgba(37, 99, 235, 0.1); color: #2563eb; font-weight: 600; padding: 4px 8px; border-radius: 4px;">
                                ${frappe.utils.escape_html(plan.grade_group)}
                            </span>
                        </td>
                        <td style="padding: 14px 16px; font-size: 13px;">
                            <span class="pms-badge ${plan.badge_class}" style="font-size: 12px; padding: 3px 10px; border-radius: 12px; font-weight: 500;">
                                ${frappe.utils.escape_html(plan.plan_status)}
                            </span>
                        </td>
                        <td style="padding: 14px 16px; font-size: 13px; color: var(--text-muted);">
                            ${frappe.utils.escape_html(plan.workflow_state)}
                        </td>
                        <td style="padding: 14px 16px; text-align: right;">
                            <button class="btn btn-xs btn-default btn-view-plan" data-name="${frappe.utils.escape_html(plan.name)}" style="border-radius: 6px; font-weight: 500; font-size: 12px;">
                                View Plan &rarr;
                            </button>
                        </td>
                    </tr>
                `;
            });
        }

        // return `
        // <div class="gdl-pms-supervisor-2-wrapper gdl-pms-dashboard-wrapper" data-pms-dashboard="supervisor-2" style="padding: 24px; max-width: 1280px; margin: 0 auto;">
        //     <!-- Top Greeting & Header Section -->
        //     <div class="pms-header-row" style="display: flex; justify-content: space-between; align-items: flex-start; margin-bottom: 24px;">
        //         <div class="pms-greeting-col">
        //             <h1 class="pms-greeting-title" style="font-size: 24px; font-weight: 700; margin: 0 0 6px 0; color: var(--text-color);">${frappe.utils.escape_html(data.greeting)} </h1>
        //             <p class="pms-greeting-subtitle" style="margin: 0; color: var(--text-muted); font-size: 14px;">Supervisor 2 Monitoring Portal &bull; Read-only observation of assigned employees' performance plans and progress.</p>
        //         </div>
        //         <div class="pms-quote-col" style="text-align: right; max-width: 320px;">
        //             <div class="pms-quote-text" style="font-style: italic; font-size: 12px; color: var(--text-muted);">"Observation and insight guide steady performance."</div>
        //         </div>
        //     </div>

        //     <!-- PMS Information Banner -->
        //     <div class="pms-info-banner" style="background: linear-gradient(135deg, #eff6ff 0%, #f8fafc 100%); border: 1px solid #bfdbfe; border-radius: 12px; padding: 16px 20px; margin-bottom: 24px; display: flex; align-items: center; gap: 16px;">
        //         <div style="font-size: 28px; line-height: 1;">ℹ️</div>
        //         <div style="flex: 1;">
        //             <div style="font-weight: 700; font-size: 14px; color: #1e3a8a; margin-bottom: 3px;">Performance Management System &bull; Observer & Monitoring Access</div>
        //             <div style="font-size: 12.5px; color: #334155; line-height: 1.5;">
        //                 You have read-only visibility to observe performance plans, KPIs, targets, and competencies for your assigned employees. All appraisal reviews and approvals are carried out by their primary Supervisor and Reviewer.
        //             </div>
        //         </div>
        //     </div>

        //     <!-- Top Stat Cards Grid (Informational & Monitoring Only) -->
        //     <div class="pms-stats-grid" style="display: grid; grid-template-columns: repeat(auto-fit, minmax(220px, 1fr)); gap: 16px; margin-bottom: 28px;">
        //         <!-- Card 1: Monitored Employees -->
        //         <div class="pms-stat-card card-blue" style="background: var(--card-bg, #ffffff); border-radius: 12px; padding: 18px; border: 1px solid var(--border-color, #e5e7eb); box-shadow: 0 1px 3px rgba(0,0,0,0.05);">
        //             <div class="pms-stat-card-header" style="display: flex; justify-content: space-between; align-items: center; margin-bottom: 12px;">
        //                 <div class="pms-icon-box box-blue" style="width: 38px; height: 38px; border-radius: 8px; display: flex; align-items: center; justify-content: center; background: rgba(37,99,235,0.1);">
        //                     <svg width="20" height="20" viewBox="0 0 24 24" fill="none" stroke="#2563eb" stroke-width="2">
        //                         <path d="M17 21v-2a4 4 0 0 0-4-4H5a4 4 0 0 0-4 4v2"></path>
        //                         <circle cx="9" cy="7" r="4"></circle>
        //                         <path d="M23 21v-2a4 4 0 0 0-3-3.87"></path>
        //                         <path d="M16 3.13a4 4 0 0 1 0 7.75"></path>
        //                     </svg>
        //                 </div>
        //                 <span style="font-size: 12px; font-weight: 600; color: #2563eb; background: rgba(37,99,235,0.08); padding: 2px 8px; border-radius: 10px;">Employees</span>
        //             </div>
        //             <div style="font-size: 26px; font-weight: 700; color: var(--text-color); line-height: 1.1;">${counts.unique_employees || 0}</div>
        //             <div style="font-size: 12.5px; color: var(--text-muted); margin-top: 4px;">Monitored Employees</div>
        //         </div>

        //         <!-- Card 2: Monitored Plans -->
        //         <div class="pms-stat-card card-purple" style="background: var(--card-bg, #ffffff); border-radius: 12px; padding: 18px; border: 1px solid var(--border-color, #e5e7eb); box-shadow: 0 1px 3px rgba(0,0,0,0.05);">
        //             <div class="pms-stat-card-header" style="display: flex; justify-content: space-between; align-items: center; margin-bottom: 12px;">
        //                 <div class="pms-icon-box box-purple" style="width: 38px; height: 38px; border-radius: 8px; display: flex; align-items: center; justify-content: center; background: rgba(147,51,234,0.1);">
        //                     <svg width="20" height="20" viewBox="0 0 24 24" fill="none" stroke="#9333ea" stroke-width="2">
        //                         <path d="M14 2H6a2 2 0 0 0-2 2v16a2 2 0 0 0 2 2h12a2 2 0 0 0 2-2V8z"></path>
        //                         <polyline points="14 2 14 8 20 8"></polyline>
        //                     </svg>
        //                 </div>
        //                 <span style="font-size: 12px; font-weight: 600; color: #9333ea; background: rgba(147,51,234,0.08); padding: 2px 8px; border-radius: 10px;">Plans</span>
        //             </div>
        //             <div style="font-size: 26px; font-weight: 700; color: var(--text-color); line-height: 1.1;">${counts.total_monitored || 0}</div>
        //             <div style="font-size: 12.5px; color: var(--text-muted); margin-top: 4px;">Total Performance Plans</div>
        //         </div>

        //         <!-- Card 3: Active PMS Cycle -->
        //         <div class="pms-stat-card card-orange" data-action="route-cycles" style="background: var(--card-bg, #ffffff); border-radius: 12px; padding: 18px; border: 1px solid var(--border-color, #e5e7eb); box-shadow: 0 1px 3px rgba(0,0,0,0.05); cursor: pointer;">
        //             <div class="pms-stat-card-header" style="display: flex; justify-content: space-between; align-items: center; margin-bottom: 12px;">
        //                 <div class="pms-icon-box box-orange" style="width: 38px; height: 38px; border-radius: 8px; display: flex; align-items: center; justify-content: center; background: rgba(217,119,6,0.1);">
        //                     <svg width="20" height="20" viewBox="0 0 24 24" fill="none" stroke="#d97706" stroke-width="2">
        //                         <rect x="3" y="4" width="18" height="18" rx="2" ry="2"></rect>
        //                         <line x1="16" y1="2" x2="16" y2="6"></line>
        //                         <line x1="8" y1="2" x2="8" y2="6"></line>
        //                         <line x1="3" y1="10" x2="21" y2="10"></line>
        //                     </svg>
        //                 </div>
        //                 <span style="font-size: 12px; font-weight: 600; color: #d97706; background: rgba(217,119,6,0.08); padding: 2px 8px; border-radius: 10px;">Cycle ↗</span>
        //             </div>
        //             <div style="font-size: 18px; font-weight: 700; color: var(--text-color); line-height: 1.2; overflow: hidden; text-overflow: ellipsis; white-space: nowrap;">${frappe.utils.escape_html(counts.active_cycle || "Active")}</div>
        //             <div style="font-size: 12.5px; color: var(--text-muted); margin-top: 4px;">Active Appraisal Cycle</div>
        //         </div>

        //         <!-- Card 4: Approved / Finalized -->
        //         <div class="pms-stat-card card-green" style="background: var(--card-bg, #ffffff); border-radius: 12px; padding: 18px; border: 1px solid var(--border-color, #e5e7eb); box-shadow: 0 1px 3px rgba(0,0,0,0.05);">
        //             <div class="pms-stat-card-header" style="display: flex; justify-content: space-between; align-items: center; margin-bottom: 12px;">
        //                 <div class="pms-icon-box box-green" style="width: 38px; height: 38px; border-radius: 8px; display: flex; align-items: center; justify-content: center; background: rgba(22,163,74,0.1);">
        //                     <svg width="20" height="20" viewBox="0 0 24 24" fill="none" stroke="#16a34a" stroke-width="2">
        //                         <path d="M22 11.08V12a10 10 0 1 1-5.93-9.14"></path>
        //                         <polyline points="22 4 12 14.01 9 11.01"></polyline>
        //                     </svg>
        //                 </div>
        //                 <span style="font-size: 12px; font-weight: 600; color: #16a34a; background: rgba(22,163,74,0.08); padding: 2px 8px; border-radius: 10px;">Approved</span>
        //             </div>
        //             <div style="font-size: 26px; font-weight: 700; color: var(--text-color); line-height: 1.1;">${counts.approved || 0}</div>
        //             <div style="font-size: 12.5px; color: var(--text-muted); margin-top: 4px;">Approved & Monitoring</div>
        //         </div>
        //     </div>

        //     <!-- Monitored Plans List Section -->
        //     <div class="pms-section-card" style="background: var(--card-bg, #ffffff); border-radius: 12px; border: 1px solid var(--border-color, #e5e7eb); box-shadow: 0 1px 3px rgba(0,0,0,0.05); overflow: hidden;">
        //         <div class="pms-card-header-flex" style="padding: 18px 20px; border-bottom: 1px solid var(--border-color, #e5e7eb); display: flex; justify-content: space-between; align-items: center;">
        //             <div class="pms-section-header" style="display: flex; align-items: center; gap: 8px;">
        //                 <h2 class="pms-section-title" style="font-size: 16px; font-weight: 700; margin: 0; color: var(--text-color);">Assigned Employees &bull; Performance Plans</h2>
        //             </div>
        //             <button class="btn btn-xs btn-default btn-view-all-list" style="border-radius: 6px; font-size: 12px;">Open Full List View &rarr;</button>
        //         </div>

        //         <div class="table-responsive" style="margin: 0;">
        //             <table class="table table-hover" style="margin: 0; width: 100%;">
        //                 <thead style="background: var(--table-header-bg, #f9fafb); font-size: 11.5px; text-transform: uppercase; letter-spacing: 0.04em; color: var(--text-muted);">
        //                     <tr>
        //                         <th style="padding: 12px 16px; font-weight: 600;">Employee</th>
        //                         <th style="padding: 12px 16px; font-weight: 600;">Cycle</th>
        //                         <th style="padding: 12px 16px; font-weight: 600;">Grade Group</th>
        //                         <th style="padding: 12px 16px; font-weight: 600;">Plan Status</th>
        //                         <th style="padding: 12px 16px; font-weight: 600;">Workflow State</th>
        //                         <th style="padding: 12px 16px; text-align: right; font-weight: 600;">Action</th>
        //                     </tr>
        //                 </thead>
        //                 <tbody>
        //                     ${rows_html}
        //                 </tbody>
        //             </table>
        //         </div>
        //     </div>
        // </div>
        // `;
        return `
        <div class="gdl-pms-supervisor-2-wrapper gdl-pms-dashboard-wrapper" data-pms-dashboard="supervisor-2" style="padding: 24px; max-width: 1280px; margin: 0 auto;">
            <!-- Top Greeting & Header Section -->
            <div class="pms-header-row" style="display: flex; justify-content: space-between; align-items: flex-start; margin-bottom: 24px;">
                <div class="pms-greeting-col">
                    <h1 class="pms-greeting-title" style="font-size: 24px; font-weight: 700; margin: 0 0 6px 0; color: var(--text-color);">${frappe.utils.escape_html(data.greeting)}</h1>
                    <p class="pms-greeting-subtitle" style="margin: 0; color: var(--text-muted); font-size: 14px;">Supervisor 2 Monitoring Portal &bull; Read-only observation of assigned employees' performance plans and progress.</p>
                </div>
                <div class="pms-quote-col" style="text-align: right; max-width: 320px;">
                    <div class="pms-quote-text" style="font-style: italic; font-size: 12px; color: var(--text-muted);">"Observation and insight guide steady performance."</div>
                </div>
            </div>

            <!-- PMS Information Banner -->
            <div class="pms-info-banner" style="background: linear-gradient(135deg, #eff6ff 0%, #f8fafc 100%); border: 1px solid #bfdbfe; border-radius: 12px; padding: 16px 20px; margin-bottom: 24px; display: flex; align-items: center; gap: 16px;">
                <div style="width: 34px; height: 34px; border-radius: 8px; background: rgba(37,99,235,0.1); display: flex; align-items: center; justify-content: center; flex-shrink: 0;">
                    <svg width="18" height="18" viewBox="0 0 24 24" fill="none" stroke="#2563eb" stroke-width="2" stroke-linecap="round" stroke-linejoin="round">
                        <circle cx="12" cy="12" r="10"></circle>
                        <line x1="12" y1="16" x2="12" y2="12"></line>
                        <line x1="12" y1="8" x2="12.01" y2="8"></line>
                    </svg>
                </div>
                <div style="flex: 1;">
                    <div style="font-weight: 700; font-size: 14px; color: #1e3a8a; margin-bottom: 3px;">Performance Management System &bull; Observer & Monitoring Access</div>
                    <div style="font-size: 12.5px; color: #334155; line-height: 1.5;">
                        You have read-only visibility to observe performance plans, KPIs, targets, and competencies for your assigned employees. All appraisal reviews and approvals are carried out by their primary Supervisor and Reviewer.
                    </div>
                </div>
            </div>

            <!-- Top Stat Cards Grid (Informational & Monitoring Only) -->
            <div class="pms-stats-grid" style="display: grid; grid-template-columns: repeat(auto-fit, minmax(220px, 1fr)); gap: 16px; margin-bottom: 28px;">
                <!-- Card 1: Monitored Employees -->
                <div class="pms-stat-card card-blue" style="background: var(--card-bg, #ffffff); border-radius: 12px; padding: 18px; border: 1px solid var(--border-color, #e5e7eb); box-shadow: 0 1px 3px rgba(0,0,0,0.05);">
                    <div class="pms-stat-card-header" style="display: flex; justify-content: space-between; align-items: center; margin-bottom: 12px;">
                        <div class="pms-icon-box box-blue" style="width: 38px; height: 38px; border-radius: 8px; display: flex; align-items: center; justify-content: center; background: rgba(37,99,235,0.1);">
                            <svg width="20" height="20" viewBox="0 0 24 24" fill="none" stroke="#2563eb" stroke-width="2">
                                <path d="M17 21v-2a4 4 0 0 0-4-4H5a4 4 0 0 0-4 4v2"></path>
                                <circle cx="9" cy="7" r="4"></circle>
                                <path d="M23 21v-2a4 4 0 0 0-3-3.87"></path>
                                <path d="M16 3.13a4 4 0 0 1 0 7.75"></path>
                            </svg>
                        </div>
                        <span style="font-size: 12px; font-weight: 600; color: #2563eb; background: rgba(37,99,235,0.08); padding: 2px 8px; border-radius: 10px;">Employees</span>
                    </div>
                    <div style="font-size: 26px; font-weight: 700; color: var(--text-color); line-height: 1.1;">${counts.unique_employees || 0}</div>
                    <div style="font-size: 12.5px; color: var(--text-muted); margin-top: 4px;">Monitored Employees</div>
                </div>

                <!-- Card 2: Monitored Plans -->
                <div class="pms-stat-card card-purple" style="background: var(--card-bg, #ffffff); border-radius: 12px; padding: 18px; border: 1px solid var(--border-color, #e5e7eb); box-shadow: 0 1px 3px rgba(0,0,0,0.05);">
                    <div class="pms-stat-card-header" style="display: flex; justify-content: space-between; align-items: center; margin-bottom: 12px;">
                        <div class="pms-icon-box box-purple" style="width: 38px; height: 38px; border-radius: 8px; display: flex; align-items: center; justify-content: center; background: rgba(147,51,234,0.1);">
                            <svg width="20" height="20" viewBox="0 0 24 24" fill="none" stroke="#9333ea" stroke-width="2">
                                <path d="M14 2H6a2 2 0 0 0-2 2v16a2 2 0 0 0 2 2h12a2 2 0 0 0 2-2V8z"></path>
                                <polyline points="14 2 14 8 20 8"></polyline>
                            </svg>
                        </div>
                        <span style="font-size: 12px; font-weight: 600; color: #9333ea; background: rgba(147,51,234,0.08); padding: 2px 8px; border-radius: 10px;">Plans</span>
                    </div>
                    <div style="font-size: 26px; font-weight: 700; color: var(--text-color); line-height: 1.1;">${counts.total_monitored || 0}</div>
                    <div style="font-size: 12.5px; color: var(--text-muted); margin-top: 4px;">Total Performance Plans</div>
                </div>

                <!-- Card 3: Active PMS Cycle -->
                <div class="pms-stat-card card-orange" data-action="route-cycles" style="background: var(--card-bg, #ffffff); border-radius: 12px; padding: 18px; border: 1px solid var(--border-color, #e5e7eb); box-shadow: 0 1px 3px rgba(0,0,0,0.05); cursor: pointer;">
                    <div class="pms-stat-card-header" style="display: flex; justify-content: space-between; align-items: center; margin-bottom: 12px;">
                        <div class="pms-icon-box box-orange" style="width: 38px; height: 38px; border-radius: 8px; display: flex; align-items: center; justify-content: center; background: rgba(217,119,6,0.1);">
                            <svg width="20" height="20" viewBox="0 0 24 24" fill="none" stroke="#d97706" stroke-width="2">
                                <rect x="3" y="4" width="18" height="18" rx="2" ry="2"></rect>
                                <line x1="16" y1="2" x2="16" y2="6"></line>
                                <line x1="8" y1="2" x2="8" y2="6"></line>
                                <line x1="3" y1="10" x2="21" y2="10"></line>
                            </svg>
                        </div>
                        <span style="font-size: 12px; font-weight: 600; color: #d97706; background: rgba(217,119,6,0.08); padding: 2px 8px; border-radius: 10px;">Cycle</span>
                    </div>
                    <div style="font-size: 18px; font-weight: 700; color: var(--text-color); line-height: 1.2; overflow: hidden; text-overflow: ellipsis; white-space: nowrap;">${frappe.utils.escape_html(counts.active_cycle || "Active")}</div>
                    <div style="font-size: 12.5px; color: var(--text-muted); margin-top: 4px;">Active Appraisal Cycle</div>
                </div>

                <!-- Card 4: Approved / Finalized -->
                <div class="pms-stat-card card-green" style="background: var(--card-bg, #ffffff); border-radius: 12px; padding: 18px; border: 1px solid var(--border-color, #e5e7eb); box-shadow: 0 1px 3px rgba(0,0,0,0.05);">
                    <div class="pms-stat-card-header" style="display: flex; justify-content: space-between; align-items: center; margin-bottom: 12px;">
                        <div class="pms-icon-box box-green" style="width: 38px; height: 38px; border-radius: 8px; display: flex; align-items: center; justify-content: center; background: rgba(22,163,74,0.1);">
                            <svg width="20" height="20" viewBox="0 0 24 24" fill="none" stroke="#16a34a" stroke-width="2">
                                <path d="M22 11.08V12a10 10 0 1 1-5.93-9.14"></path>
                                <polyline points="22 4 12 14.01 9 11.01"></polyline>
                            </svg>
                        </div>
                        <span style="font-size: 12px; font-weight: 600; color: #16a34a; background: rgba(22,163,74,0.08); padding: 2px 8px; border-radius: 10px;">Approved</span>
                    </div>
                    <div style="font-size: 26px; font-weight: 700; color: var(--text-color); line-height: 1.1;">${counts.approved || 0}</div>
                    <div style="font-size: 12.5px; color: var(--text-muted); margin-top: 4px;">Approved & Monitoring</div>
                </div>
            </div>

            <!-- Monitored Plans List Section -->
            <div class="pms-section-card" style="background: var(--card-bg, #ffffff); border-radius: 12px; border: 1px solid var(--border-color, #e5e7eb); box-shadow: 0 1px 3px rgba(0,0,0,0.05); overflow: hidden;">
                <div class="pms-card-header-flex" style="padding: 18px 20px; border-bottom: 1px solid var(--border-color, #e5e7eb); display: flex; justify-content: space-between; align-items: center;">
                    <div class="pms-section-header" style="display: flex; align-items: center; gap: 8px;">
                        <h2 class="pms-section-title" style="font-size: 16px; font-weight: 700; margin: 0; color: var(--text-color);">Assigned Employees &bull; Performance Plans</h2>
                    </div>
                    <button class="btn btn-xs btn-default btn-view-all-list" style="border-radius: 6px; font-size: 12px; display: inline-flex; align-items: center; gap: 6px;">
                        Open Full List View
                        <svg width="12" height="12" viewBox="0 0 24 24" fill="none" stroke="currentColor" stroke-width="2.5">
                            <path d="M5 12h14M13 6l6 6-6 6"/>
                        </svg>
                    </button>
                </div>

                <div class="table-responsive" style="margin: 0;">
                    <table class="table table-hover" style="margin: 0; width: 100%;">
                        <thead style="background: var(--table-header-bg, #f9fafb); font-size: 11.5px; text-transform: uppercase; letter-spacing: 0.04em; color: var(--text-muted);">
                            <tr>
                                <th style="padding: 12px 16px; font-weight: 600;">Employee</th>
                                <th style="padding: 12px 16px; font-weight: 600;">Cycle</th>
                                <th style="padding: 12px 16px; font-weight: 600;">Grade Group</th>
                                <th style="padding: 12px 16px; font-weight: 600;">Plan Status</th>
                                <th style="padding: 12px 16px; font-weight: 600;">Workflow State</th>
                                <th style="padding: 12px 16px; text-align: right; font-weight: 600;">Action</th>
                            </tr>
                        </thead>
                        <tbody>
                            ${rows_html}
                        </tbody>
                    </table>
                </div>
            </div>
        </div>
        `;
    },

    bind_events: function ($container) {
        $container.find('[data-action="route-cycles"]').on('click', function (e) {
            e.stopPropagation();
            frappe.set_route('List', 'PMS Appraisal Cycle');
        });

        $container.find('.pms-monitoring-row').on('click', function (e) {
            var name = $(this).data('name');
            if (name) {
                frappe.set_route('Form', 'PMS Appraisal', name);
            }
        });

        $container.find('.btn-view-all-list').on('click', function (e) {
            e.stopPropagation();
            frappe.set_route('List', 'PMS Appraisal');
        });
    }
};
