(function () {
    if (typeof window === 'undefined' || !window.frappe) return;

    var PMS_DASHBOARD_ROUTES = ['pms-hr', 'pms-reviewer', 'pms-supervisor-2', 'pms-supervisor', 'pms-employee'];

    function get_pms_target_route() {
        if (!window.frappe || !frappe.session || !frappe.session.user || frappe.session.user === 'Guest') {
            return null;
        }

        var roles = frappe.user_roles || (frappe.boot && frappe.boot.user && frappe.boot.user.roles) || [];

        // 1. HR Admin / HR Manager -> HR Dashboard
        if (roles.indexOf('HR Admin') !== -1 || roles.indexOf('HR Manager') !== -1 || roles.indexOf('PMS HR') !== -1) {
            return 'pms-hr';
        }

        // 2. Reviewer -> Reviewer Dashboard
        if (roles.indexOf('Reviewer') !== -1 || roles.indexOf('PMS Reviewer') !== -1) {
            return 'pms-reviewer';
        }

        // 3. Supervisor 2 -> Supervisor 2 Dashboard
        if (roles.indexOf('Supervisor 2') !== -1) {
            return 'pms-supervisor-2';
        }

        // 4. Supervisor -> Supervisor Dashboard
        if (roles.indexOf('Supervisor') !== -1) {
            return 'pms-supervisor';
        }

        // 5. Employee -> Employee Dashboard
        if (roles.indexOf('Employee') !== -1 || roles.indexOf('PMS Employee') !== -1) {
            return 'pms-employee';
        }

        // 6. Admin / System Manager fallback to HR Dashboard in PMS context
        if (roles.indexOf('Administrator') !== -1 || roles.indexOf('System Manager') !== -1) {
            return 'pms-hr';
        }

        return null;
    }

    function patch_breadcrumbs() {
        if (!window.frappe || !frappe.breadcrumbs) return;
        if (frappe.breadcrumbs._pms_home_patched) return;
        frappe.breadcrumbs._pms_home_patched = true;

        var orig_clear = frappe.breadcrumbs.clear;
        frappe.breadcrumbs.clear = function () {
            this.$breadcrumbs = $(".navbar-breadcrumbs").empty();
            var target = get_pms_target_route();
            var home_url = target ? ("/desk/" + target) : "/desk";
            this.append_breadcrumb_element(home_url, frappe.utils.icon("home"), "pms-home-crumb");
        };
    }

    function update_existing_home_crumb() {
        var target = get_pms_target_route();
        if (!target) return;
        var homeCrumbA = document.querySelector('.navbar-breadcrumbs li:first-child a, .navbar-breadcrumbs a.pms-home-crumb');
        if (homeCrumbA) {
            homeCrumbA.setAttribute('href', '/desk/' + target);
        }
    }

    function patch_not_found() {
        if (!window.frappe) return;
        if (frappe.show_not_found && !frappe.show_not_found._pms_patched) {
            var orig_show_not_found = frappe.show_not_found;
            frappe.show_not_found = function (name) {
                var target = get_pms_target_route();
                var name_str = (name || '').toString().toLowerCase();
                if (target && (name_str.indexOf('pms-') !== -1 || name_str === 'workspaces' || name_str === 'desktop')) {
                    console.log('[GDL PMS] Intercepted 404 for ' + name + ', redirecting to target dashboard ' + target);
                    if (frappe.ui && frappe.ui.hide_open_dialog) frappe.ui.hide_open_dialog();
                    $('.modal:visible').modal('hide');
                    frappe.set_route(target);
                    return;
                }
                return orig_show_not_found.apply(this, arguments);
            };
            frappe.show_not_found._pms_patched = true;
        }
    }

    function patch_router() {
        if (!window.frappe) return;

        if (frappe.set_route && !frappe.set_route._pms_router_patched) {
            var orig_set_route = frappe.set_route;
            frappe.set_route = function () {
                var args = Array.from(arguments);
                var target = get_pms_target_route();
                if (target) {
                    var r = args.length === 1 && Array.isArray(args[0]) ? args[0] : args;
                    var first = (r[0] || '').toString().toLowerCase().replace(/^\/+|\/+$/g, '');
                    if (!r.length || first === '' || first === 'desk' || first === 'app' || first === 'desktop' || first === 'workspaces') {
                        return orig_set_route.call(this, target);
                    }
                }
                return orig_set_route.apply(this, arguments);
            };
            frappe.set_route._pms_router_patched = true;
        }

        if (frappe.router && frappe.router.set_route && !frappe.router.set_route._pms_router_patched) {
            var orig_router_set_route = frappe.router.set_route;
            frappe.router.set_route = function () {
                var args = Array.from(arguments);
                var target = get_pms_target_route();
                if (target) {
                    var r = args.length === 1 && Array.isArray(args[0]) ? args[0] : args;
                    var first = (r[0] || '').toString().toLowerCase().replace(/^\/+|\/+$/g, '');
                    if (!r.length || first === '' || first === 'desk' || first === 'app' || first === 'desktop' || first === 'workspaces') {
                        return orig_router_set_route.call(this, target);
                    }
                }
                return orig_router_set_route.apply(this, arguments);
            };
            frappe.router.set_route._pms_router_patched = true;
        }
    }

    function check_and_redirect_to_dashboard() {
        var target = get_pms_target_route();
        if (!target) return;

        patch_breadcrumbs();
        patch_router();
        patch_not_found();
        update_existing_home_crumb();

        var route = (frappe.get_route && frappe.get_route()) || [];
        var first = (route[0] || '').toLowerCase();
        var pathname = (window.location.pathname || '').replace(/\/+$/, '');

        // 1. If at /desk, /app, /apps or empty desk route
        var is_desk_root = (!route.length || first === '' || first === 'desk' || first === 'desktop' || first === 'app' || first === 'apps' || first === 'workspaces');
        var is_desk_path = (pathname === '' || pathname === '/desk' || pathname === '/app' || pathname === '/apps');

        if (is_desk_root && is_desk_path) {
            if (frappe.router && frappe.router.set_route) {
                frappe.set_route(target);
            } else {
                window.location.replace('/desk/' + target);
            }
            return;
        }

        // 2. Cross-role mismatch protection: If an HR Admin visits another role's dashboard (e.g. /desk/pms-employee from previous session), redirect to own dashboard!
        if (PMS_DASHBOARD_ROUTES.indexOf(first) !== -1 && first !== target) {
            console.log('[GDL PMS] Role dashboard mismatch (' + first + ' vs ' + target + '), auto-redirecting to ' + target);
            if (frappe.router && frappe.router.set_route) {
                frappe.set_route(target);
            } else {
                window.location.replace('/desk/' + target);
            }
            return;
        }

        // 3. Pathname check for mismatch
        for (var i = 0; i < PMS_DASHBOARD_ROUTES.length; i++) {
            var slug = PMS_DASHBOARD_ROUTES[i];
            if (slug !== target && (pathname === '/desk/' + slug || pathname === '/app/' + slug)) {
                window.location.replace('/desk/' + target);
                return;
            }
        }
    }

    // Capture-phase listener to intercept home icon & desk links before ANY router handlers
    document.addEventListener('click', function (e) {
        var targetRoute = get_pms_target_route();
        if (!targetRoute) return;

        var homeEl = e.target.closest(
            '.navbar-breadcrumbs li:first-child a, ' +
            '.navbar-breadcrumbs li:first-child, ' +
            '.pms-home-crumb, ' +
            'a[href="/desk"], a[href="/app"], ' +
            'a[href="/desk/"], a[href="/app/"], ' +
            '.navbar-brand, .app-logo, .nav-item-home, ' +
            '[data-route="Workspaces"], [data-route="desk"]'
        );

        if (homeEl) {
            e.preventDefault();
            e.stopPropagation();
            e.stopImmediatePropagation();

            if (window.frappe && frappe.set_route) {
                frappe.set_route(targetRoute);
            } else {
                window.location.href = '/desk/' + targetRoute;
            }
            return false;
        }
    }, true);

    function update_pms_sidebar_highlight(mode) {
        setTimeout(function () {
            var $sidebar = $('.body-sidebar, .desk-sidebar');
            if (!$sidebar.length) return;
            var $planItem = $sidebar.find('.sidebar-item-container[item-name="PMS Performance Plan"] .standard-sidebar-item');
            var $appraisalItem = $sidebar.find('.sidebar-item-container[item-name="PMS Appraisal Form"] .standard-sidebar-item');
            if (mode === 'appraisal') {
                $planItem.removeClass('active-sidebar selected');
                $appraisalItem.addClass('active-sidebar selected');
            } else if (mode === 'plan') {
                $appraisalItem.removeClass('active-sidebar selected');
                $planItem.addClass('active-sidebar selected');
            }
        }, 50);
    }

    // Intercept clicks on Sidebar items & shortcuts for PMS Performance Plan vs PMS Appraisal Form
    document.addEventListener('click', function (e) {
        var sidebarContainer = e.target.closest('.sidebar-item-container, .standard-sidebar-item, .shortcut-widget-box');
        if (!sidebarContainer) return;

        var itemName = sidebarContainer.getAttribute('item-name') || '';
        var text = (sidebarContainer.innerText || sidebarContainer.textContent || '').trim();

        var target_mode = null;
        if (itemName === 'PMS Appraisal Form' || text.indexOf('PMS Appraisal Form') !== -1 || text.indexOf('Appraisal Form') !== -1) {
            target_mode = 'appraisal';
        } else if (itemName === 'PMS Performance Plan' || text.indexOf('PMS Performance Plan') !== -1 || text.indexOf('Performance Plan') !== -1) {
            target_mode = 'plan';
        }

        if (!target_mode) return;

        e.preventDefault();
        e.stopPropagation();
        e.stopImmediatePropagation();

        localStorage.setItem('pms_view_mode', target_mode);
        if (window.frappe) {
            frappe.route_options = { view_mode: target_mode };
        }

        update_pms_sidebar_highlight(target_mode);

        var route = (frappe.get_route && frappe.get_route()) || [];
        var is_on_pms_appraisal_list = (typeof cur_list !== 'undefined' && cur_list && cur_list.doctype === 'PMS Appraisal') ||
            (route.length >= 2 && (route[0] || '').toLowerCase() === 'list' && route[1] === 'PMS Appraisal');

        if (is_on_pms_appraisal_list && typeof cur_list !== 'undefined' && cur_list && cur_list.apply_pms_view_mode) {
            cur_list.apply_pms_view_mode(target_mode, true);
        } else if (window.frappe && frappe.set_route) {
            frappe.set_route('List', 'PMS Appraisal', 'List');
        } else {
            window.location.href = '/desk/pms-appraisal/view/list';
        }
        return false;
    }, true);

    // Check on route changes & app initialization
    $(document).on('app_ready page-change ajaxComplete', function () {
        check_and_redirect_to_dashboard();
    });

    if (window.frappe && frappe.router) {
        frappe.router.on('change', function () {
            check_and_redirect_to_dashboard();
        });
    }

    // Immediate and staggered initialization checks
    patch_breadcrumbs();
    patch_router();
    patch_not_found();
    check_and_redirect_to_dashboard();
    setTimeout(check_and_redirect_to_dashboard, 100);
    setTimeout(check_and_redirect_to_dashboard, 300);
    setTimeout(check_and_redirect_to_dashboard, 800);
})();
