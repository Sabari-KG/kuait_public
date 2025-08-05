/** @odoo-module **/

import { patch } from "@web/core/utils/patch";
import { ListController } from '@web/views/list/list_controller';
import { MenuDropdown } from '@web/webclient/navbar/navbar';
import { onWillStart, onWillUnmount, onWillRender, useEffect, onMounted } from "@odoo/owl";
import { NavBar } from "@web/webclient/navbar/navbar";

export function dnNavBarAddClasses(){
    $('body').addClass('ks_body_class');
    $('.o_main_navbar').addClass('navbar navbar-expand-md');
    $('.apps-menu-icon-default').addClass('d-none');
    $('.ks-apps-menu-icon').removeClass('d-none');
    $('.ks_user_avatar_default').addClass('d-none');
    $('.ks_user_avatar').removeClass('d-none');
    $('.comments-systray-default').addClass('d-none');
    $('.ks-comments-systray').removeClass('d-none');
    $('.mail-systray-default').addClass('d-none');
    $('.ks-mail-systray').removeClass('d-none');
    $('.ks-mobile-burger-menu').removeClass('d-none');
    $('.mobile-burger-menu-default').addClass('d-none');
}



export function dnNavBarRemoveClasses(){
    $('body').removeClass('ks_body_class');
    $('.apps-menu-icon-default').removeClass('d-none');
    $('.ks-apps-menu-icon').addClass('d-none');
    $('.ks_user_avatar_default').removeClass('d-none');
    $('.ks_user_avatar').addClass('d-none');
    $('.mail-systray-default').removeClass('d-none');
    $('.ks-mail-systray').addClass('d-none');
    $('.comments-systray-default').removeClass('d-none');
    $('.ks-comments-systray').addClass('d-none');
    $('.o_main_navbar').removeClass('navbar navbar-expand-md');
    $('.ks-mobile-burger-menu').addClass('d-none');
    $('.mobile-burger-menu-default').removeClass('d-none');
}


patch(MenuDropdown.prototype,{
    setup() {
        super.setup();
        useEffect(
            () => {
                if(this.props?.slots?.toggler?.__ctx?.section?.childrenTree?.length >= 9)
                    $(this.rootRef?.el)?.addClass('mega-menu dash-dd');
                else
                    $(this.rootRef?.el)?.addClass(' dash-dd');
            },
            () => []
        );
    },

});

patch(NavBar.prototype,{
    async adapt(){
        if(this.currentApp?.xmlid === "ks_dashboard_ninja.board_menu_root"){
            if(!$('body').hasClass('ks_body_class'))
                dnNavBarAddClasses();
        }
        else{
            if($('body').hasClass('ks_body_class'))
                dnNavBarRemoveClasses();
        }
        return super.adapt();
    },

    onNavBarDropdownItemSelection(menu) {
        if(this.currentApp?.xmlid === "ks_dashboard_ninja.board_menu_root"){
            if(!$('body').hasClass('ks_body_class'))
                dnNavBarAddClasses();
        }
        else{
            if($('body').hasClass('ks_body_class'))
                dnNavBarRemoveClasses();
        }
        super.onNavBarDropdownItemSelection(menu);
    }



});

