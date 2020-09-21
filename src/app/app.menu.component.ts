import { Component, Input, OnInit, AfterViewInit, ViewChild } from '@angular/core';
import { trigger, state, style, transition, animate } from '@angular/animations';
import { MenuItem, ScrollPanel } from 'primeng/primeng';
import { AppMainComponent } from './app.main.component';

@Component({
    selector: 'app-menu',
    templateUrl: './app.menu.component.html',
    animations: [
        trigger('inline', [
            state('hiddenAnimated', style({
                height: '0px',
                overflow: 'hidden'
            })),
            state('visibleAnimated', style({
                height: '*',
            })),
            transition('visibleAnimated => hiddenAnimated', animate('400ms cubic-bezier(0.86, 0, 0.07, 1)')),
            transition('hiddenAnimated => visibleAnimated', animate('400ms cubic-bezier(0.86, 0, 0.07, 1)'))
        ])
    ]
})
export class AppMenuComponent implements OnInit, AfterViewInit {

    @Input() reset: boolean;

    model: any[];

    inlineModel: any[];

    inlineUserMenuActive = false;

    @ViewChild('layoutMenuScroller') layoutMenuScrollerViewChild: ScrollPanel;

    constructor(public app: AppMainComponent) { }

    ngOnInit() {
        this.model = [
            { label: 'Dashboard', icon: 'pi pi-fw pi-home', routerLink: ['/']},
            {
                label: 'Layouts', icon: 'pi pi-fw pi-th-large',
                items: [
                    { label: 'Static', icon: 'pi pi-fw pi-bars', command: event => this.app.changeMenuMode('static') },
                    { label: 'Overlay', icon: 'pi pi-fw pi-bars', command: event => this.app.changeMenuMode('overlay') },
                    { label: 'Slim', icon: 'pi pi-fw pi-bars', command: event => {
                        this.app.changeMenuMode('slim');
                        this.app.inlineUser = false;
                        this.inlineUserMenuActive = false;
                    }},
                    { label: 'Horizontal', icon: 'pi pi-fw pi-bars', command: event => {
                        this.app.changeMenuMode('horizontal');
                        this.app.inlineUser = false;
                        this.inlineUserMenuActive = false;
                    }},
                    {
                        label: 'Orientation', icon: 'pi pi-fw pi-align-right',
                        items: [
                            {label: 'LTR', icon: 'pi pi-fw pi-align-left', command: (event) => {this.app.isRTL = false; }},
                            {label: 'RTL', icon: 'pi pi-fw pi-align-right', command: (event) => {this.app.isRTL = true; }}
                        ]
                    }
                ]
            },
            {
                label: 'Topbar Colors', icon: 'pi pi-fw pi-pencil',
                items: [
                    {
                        label: 'Light', icon: 'pi pi-fw pi-pencil',
                        command: (event) => this.changeTopbarColor('layout-topbar-light', 'logo-roma')
                    },
                    {
                        label: 'Dark', icon: 'pi pi-fw pi-pencil',
                        command: (event) => this.changeTopbarColor('layout-topbar-dark', 'logo-roma-white')
                    },
                    {
                        label: 'Blue', icon: 'pi pi-fw pi-pencil',
                        command: (event) => this.changeTopbarColor('layout-topbar-blue', 'logo-roma-white')
                    },
                    {
                        label: 'Green', icon: 'pi pi-fw pi-pencil',
                        command: (event) => this.changeTopbarColor('layout-topbar-green', 'logo-roma-white')
                    },
                    {
                        label: 'Orange', icon: 'pi pi-fw pi-pencil',
                        command: (event) => this.changeTopbarColor('layout-topbar-orange', 'logo-roma-white')
                    },
                    {
                        label: 'Magenta', icon: 'pi pi-fw pi-pencil',
                        command: (event) => this.changeTopbarColor('layout-topbar-magenta', 'logo-roma-white')
                    },
                    {
                        label: 'Blue Grey', icon: 'pi pi-fw pi-pencil',
                        command: (event) => this.changeTopbarColor('layout-topbar-bluegrey', 'logo-roma-white')
                    },
                    {
                        label: 'Deep Purple', icon: 'pi pi-fw pi-pencil',
                        command: (event) => this.changeTopbarColor('layout-topbar-deeppurple', 'logo-roma-white')
                    },
                    {
                        label: 'Brown', icon: 'pi pi-fw pi-pencil',
                        command: (event) => this.changeTopbarColor('layout-topbar-brown', 'logo-roma-white')
                    },
                    {
                        label: 'Lime', icon: 'pi pi-fw pi-pencil',
                        command: (event) => this.changeTopbarColor('layout-topbar-lime', 'logo-roma-white')
                    },
                    {
                        label: 'Rose', icon: 'pi pi-fw pi-pencil',
                        command: (event) => this.changeTopbarColor('layout-topbar-rose', 'logo-roma-white')
                    },
                    {
                        label: 'Cyan', icon: 'pi pi-fw pi-pencil',
                        command: (event) => this.changeTopbarColor('layout-topbar-cyan', 'logo-roma-white')
                    },
                    {
                        label: 'Teal', icon: 'pi pi-fw pi-pencil',
                        command: (event) => this.changeTopbarColor('layout-topbar-teal', 'logo-roma-white')
                    },
                    {
                        label: 'Deep Orange', icon: 'pi pi-fw pi-pencil',
                        command: (event) => this.changeTopbarColor('layout-topbar-deeporange', 'logo-roma-white')
                    },
                    {
                        label: 'Indigo', icon: 'pi pi-fw pi-pencil',
                        command: (event) => this.changeTopbarColor('layout-topbar-indigo', 'logo-roma-white')
                    },
                    {
                        label: 'Pink', icon: 'pi pi-fw pi-pencil',
                        command: (event) => this.changeTopbarColor('layout-topbar-pink', 'logo-roma-white')
                    },
                    {
                        label: 'Purple', icon: 'pi pi-fw pi-pencil',
                        command: (event) => this.changeTopbarColor('layout-topbar-purple', 'logo-roma-white')
                    }
                ]
            },
            {
                label: 'Menu Colors', icon: 'pi pi-fw pi-list',
                items: [
                    { label: 'Light', icon: 'pi pi-fw pi-circle-off', command: event => this.app.lightMenu = true },
                    { label: 'Dark', icon: 'pi pi-fw pi-circle-on', command: event => this.app.lightMenu = false }
                ]
            },
            {
                label: 'User Profile', icon: 'pi pi-fw pi-user',
                items: [
                    { label: 'Popup', icon: 'pi pi-fw pi-user', command: event => {
                        this.app.inlineUser = false;
                        this.inlineUserMenuActive = false;
                    }},
                    { label: 'Inline', icon: 'pi pi-fw pi-user', command: event => {
                        if (this.app.isStatic() || this.app.isOverlay()) {
                            this.app.inlineUser = true;
                        }
                    }}
                ]
            },
            {
                label: 'Theme', icon: 'pi pi-fw pi-pencil',
                items: [
                    {
                        label: 'Blue', icon: 'pi pi-fw pi-pencil',
                        command: (event) => this.changeTheme('blue')
                    },
                    {
                        label: 'Green', icon: 'pi pi-fw pi-pencil',
                        command: (event) => this.changeTheme('green')
                    },
                    {
                        label: 'Orange', icon: 'pi pi-fw pi-pencil',
                        command: (event) => this.changeTheme('orange')
                    },
                    {
                        label: 'Magenta', icon: 'pi pi-fw pi-pencil',
                        command: (event) => this.changeTheme('magenta')
                    },
                    {
                        label: 'Blue Grey', icon: 'pi pi-fw pi-pencil',
                        command: (event) => this.changeTheme('bluegrey')
                    },
                    {
                        label: 'Deep Purple', icon: 'pi pi-fw pi-pencil',
                        command: (event) => this.changeTheme('deeppurple')
                    },
                    {
                        label: 'Brown', icon: 'pi pi-fw pi-pencil',
                        command: (event) => this.changeTheme('brown')
                    },
                    {
                        label: 'Lime', icon: 'pi pi-fw pi-pencil',
                        command: (event) => this.changeTheme('lime')
                    },
                    {
                        label: 'Rose', icon: 'pi pi-fw pi-pencil',
                        command: (event) => this.changeTheme('rose')
                    },
                    {
                        label: 'Cyan', icon: 'pi pi-fw pi-pencil',
                        command: (event) => this.changeTheme('cyan')
                    },
                    {
                        label: 'Teal', icon: 'pi pi-fw pi-pencil',
                        command: (event) => this.changeTheme('teal')
                    },
                    {
                        label: 'Deep-Orange', icon: 'pi pi-fw pi-pencil',
                        command: (event) => this.changeTheme('deeporange')
                    },
                    {
                        label: 'Indigo', icon: 'pi pi-fw pi-pencil',
                        command: (event) => this.changeTheme('indigo')
                    },
                    {
                        label: 'Pink', icon: 'pi pi-fw pi-pencil',
                        command: (event) => this.changeTheme('pink')
                    },
                    {
                        label: 'Purple', icon: 'pi pi-fw pi-pencil',
                        command: (event) => this.changeTheme('purple')
                    }
                ]
            },
            {
                label: 'Components', icon: 'pi pi-fw pi-star',
                items: [
                    { label: 'Sample Page', icon: 'pi pi-fw pi-th-large', routerLink: ['/sample']  },
                    { label: 'Forms', icon: 'pi pi-fw pi-file', routerLink: ['/forms'] },
                    { label: 'Data', icon: 'pi pi-fw pi-table', routerLink: ['/data'] },
                    { label: 'Panels', icon: 'pi pi-fw pi-list', routerLink: ['/panels'] },
                    { label: 'Overlays', icon: 'pi pi-fw pi-clone', routerLink: ['/overlays'] },
                    { label: 'Menus', icon: 'pi pi-fw pi-plus', routerLink: ['/menus'] },
                    { label: 'Messages', icon: 'pi pi-fw pi-envelope', routerLink: ['/messages'] },
                    { label: 'Charts', icon: 'pi pi-fw pi-chart-bar', routerLink: ['/charts'] },
                    { label: 'File', icon: 'pi pi-fw pi-upload', routerLink: ['/file'] },
                    { label: 'Misc', icon: 'pi pi-fw pi-spinner', routerLink: ['/misc'] }
                ]
            },
            {
                label: 'Pages', icon: 'pi pi-fw pi-copy',
                items: [
                    { label: 'Empty', icon: 'pi pi-fw pi-clone', routerLink: ['/empty'] },
                    { label: 'Login', icon: 'pi pi-fw pi-sign-in', routerLink: ['/login'], target: '_blank' },
                    { label: 'Landing', icon: 'pi pi-fw pi-globe', url: 'assets/pages/landing.html', target: '_blank' },
                    { label: 'Error', icon: 'pi pi-fw pi-exclamation-triangle', routerLink: ['/error'], target: '_blank' },
                    { label: '404', icon: 'pi pi-fw pi-times', routerLink: ['/404'], target: '_blank' },
                    {
                        label: 'Access Denied', icon: 'pi pi-fw pi-ban',
                        routerLink: ['/accessdenied'], target: '_blank'
                    }
                ]
            },
            {
                label: 'Hierarchy', icon: 'pi pi-fw pi-sitemap',
                items: [
                    {
                        label: 'Submenu 1', icon: 'pi pi-fw pi-sign-in',
                        items: [
                            {
                                label: 'Submenu 1.1', icon: 'pi pi-fw pi-sign-in',
                                items: [
                                    { label: 'Submenu 1.1.1', icon: 'pi pi-fw pi-sign-in' },
                                    { label: 'Submenu 1.1.2', icon: 'pi pi-fw pi-sign-in' },
                                    { label: 'Submenu 1.1.3', icon: 'pi pi-fw pi-sign-in' },
                                ]
                            },
                            {
                                label: 'Submenu 1.2', icon: 'pi pi-fw pi-sign-in',
                                items: [
                                    { label: 'Submenu 1.2.1', icon: 'pi pi-fw pi-sign-in' }
                                ]
                            },
                        ]
                    },
                    {
                        label: 'Submenu 2', icon: 'pi pi-fw pi-sign-in',
                        items: [
                            {
                                label: 'Submenu 2.1', icon: 'pi pi-fw pi-sign-in',
                                items: [
                                    { label: 'Submenu 2.1.1', icon: 'pi pi-fw pi-sign-in' },
                                    { label: 'Submenu 2.1.2', icon: 'pi pi-fw pi-sign-in' },
                                ]
                            },
                            {
                                label: 'Submenu 2.2', icon: 'pi pi-fw pi-sign-in',
                                items: [
                                    { label: 'Submenu 2.2.1', icon: 'pi pi-fw pi-sign-in' },
                                ]
                            },
                        ]
                    }
                ]
            },
            {
                label: 'Docs', icon: 'pi pi-fw pi-file', routerLink: ['/documentation']
            },
            {
                label: 'Buy Now', icon: 'pi pi-fw pi-money-bill', url: ['https://www.primefaces.org/store']
            }
        ];
        this.inlineModel = [
            {
                label: 'Profile', icon: 'pi pi-fw pi-user'
            },
            {
                label: 'Settings', icon: 'pi pi-fw pi-cog'
            },
            {
                label: 'Messages', icon: 'pi pi-fw pi-envelope'
            },
            {
                label: 'Notifications', icon: 'pi pi-fw pi-bell'
            }
        ];
    }

    ngAfterViewInit() {
        setTimeout(() => { this.layoutMenuScrollerViewChild.moveBar(); }, 100);
    }

    changeTheme(theme: string) {
        const layoutLink: HTMLLinkElement = <HTMLLinkElement>document.getElementById('layout-css');
        layoutLink.href = 'assets/layout/css/layout-' + theme + '.css';
        const themeLink: HTMLLinkElement = <HTMLLinkElement>document.getElementById('theme-css');
        themeLink.href = 'assets/theme/' + 'theme-' + theme + '.css';
    }

    changeTopbarColor(topbarColor, logo) {
        this.app.topbarColor = topbarColor;
        const topbarLogoLink: HTMLImageElement = <HTMLImageElement>document.getElementById('topbar-logo');
        topbarLogoLink.src = 'assets/layout/images/' + logo + '.svg';
    }

    onMenuClick(event) {
        if (!this.app.isHorizontal()) {
            setTimeout(() => {
                this.layoutMenuScrollerViewChild.moveBar();
            }, 450);
        }
        this.app.onMenuClick(event);
    }
}

@Component({
    /* tslint:disable:component-selector */
    selector: '[app-submenu]',
    /* tslint:enable:component-selector */
    template: `
        <ng-template ngFor let-child let-i="index" [ngForOf]="(root ? item : item.items)">
            <li [ngClass]="{'active-menuitem': isActive(i)}" [class]="child.badgeStyleClass" *ngIf="child.visible === false ? false : true">
                <a [href]="child.url||'#'" (click)="itemClick($event,child,i)" (mouseenter)="onMouseEnter(i)"
                   *ngIf="!child.routerLink" [ngClass]="child.styleClass"
                   [attr.tabindex]="!visible ? '-1' : null" [attr.target]="child.target">
                    <i [ngClass]="child.icon" class="layout-menuitem-icon"></i>
                    <span class="layout-menuitem-text">{{child.label}}</span>
                    <i class="pi pi-fw pi-angle-down layout-submenu-toggler" *ngIf="child.items"></i>
                </a>
                <a (click)="itemClick($event,child,i)" (mouseenter)="onMouseEnter(i)" *ngIf="child.routerLink"
                   [routerLink]="child.routerLink" routerLinkActive="active-menuitem-routerlink" [fragment]="child.fragment"
                   [routerLinkActiveOptions]="{exact: true}" [attr.tabindex]="!visible ? '-1' : null" [attr.target]="child.target">
                    <i [ngClass]="child.icon" class="layout-menuitem-icon"></i>
                    <span class="layout-menuitem-text">{{child.label}}</span>
                    <i class="pi pi-fw pi-angle-down layout-submenu-toggler" *ngIf="child.items"></i>
                </a>
                <div class="layout-menu-tooltip">
                    <div class="layout-menu-tooltip-arrow"></div>
                    <div class="layout-menu-tooltip-text">{{child.label}}</div>
                </div>
                <ul app-submenu [item]="child" *ngIf="child.items" [visible]="isActive(i)" [reset]="reset" [parentActive]="isActive(i)"
                    [@children]="(app.isSlim()||app.isHorizontal())&&root ? isActive(i) ?
                    'visible' : 'hidden' : isActive(i) ? 'visibleAnimated' : 'hiddenAnimated'"></ul>
            </li>
        </ng-template>
    `,
    animations: [
        trigger('children', [
            state('hiddenAnimated', style({
                height: '0px'
            })),
            state('visibleAnimated', style({
                height: '*'
            })),
            state('visible', style({
                height: '*',
                'z-index': 100
            })),
            state('hidden', style({
                height: '0px',
                'z-index': '*'
            })),
            transition('visibleAnimated => hiddenAnimated', animate('400ms cubic-bezier(0.86, 0, 0.07, 1)')),
            transition('hiddenAnimated => visibleAnimated', animate('400ms cubic-bezier(0.86, 0, 0.07, 1)'))
        ])
    ]
})
export class AppSubMenuComponent {

    @Input() item: MenuItem;

    @Input() root: boolean;

    @Input() visible: boolean;

    _parentActive: boolean;

    _reset: boolean;

    activeIndex: number;

    constructor(public app: AppMainComponent, public appMenu: AppMenuComponent) { }

    itemClick(event: Event, item: MenuItem, index: number) {
        if (this.root) {
            this.app.menuHoverActive = !this.app.menuHoverActive;
        }

        // avoid processing disabled items
        if (item.disabled) {
            event.preventDefault();
            return true;
        }

        // activate current item and deactivate active sibling if any
        this.activeIndex = (this.activeIndex === index) ? null : index;

        // execute command
        if (item.command) {
            item.command({ originalEvent: event, item: item });
        }

        // prevent hash change
        if (item.items || (!item.url && !item.routerLink)) {
            setTimeout(() => {
                this.appMenu.layoutMenuScrollerViewChild.moveBar();
            }, 450);
            event.preventDefault();
        }

        // hide menu
        if (!item.items) {
            if (this.app.isHorizontal() || this.app.isSlim()) {
                this.app.resetMenu = true;
            }
            else {
                this.app.resetMenu = false;
            }

            this.app.overlayMenuActive = false;
            this.app.staticMenuMobileActive = false;
            this.app.menuHoverActive = !this.app.menuHoverActive;
            this.app.unblockBodyScroll();
        }
    }

    onMouseEnter(index: number) {
        if (this.root && this.app.menuHoverActive && (this.app.isHorizontal() || this.app.isSlim())
            && !this.app.isMobile() && !this.app.isTablet()) {
            this.activeIndex = index;
        }
    }

    isActive(index: number): boolean {
        return this.activeIndex === index;
    }

    @Input() get reset(): boolean {
        return this._reset;
    }

    set reset(val: boolean) {
        this._reset = val;
        if (this._reset && (this.app.isHorizontal() || this.app.isSlim())) {
            this.activeIndex = null;
        }
    }

    @Input() get parentActive(): boolean {
        return this._parentActive;
    }
    set parentActive(val: boolean) {
        this._parentActive = val;
        if (!this._parentActive) {
            this.activeIndex = null;
        }
    }
}
