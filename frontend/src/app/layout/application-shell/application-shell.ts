import { BreakpointObserver } from '@angular/cdk/layout';
import { DatePipe } from '@angular/common';
import { Component, computed, inject, signal } from '@angular/core';
import { MatButtonModule } from '@angular/material/button';
import { MatDividerModule } from '@angular/material/divider';
import { MatMenuModule } from '@angular/material/menu';
import { MatSidenavModule } from '@angular/material/sidenav';
import { MatToolbarModule } from '@angular/material/toolbar';
import { MatTooltipModule } from '@angular/material/tooltip';
import {
  LucideDatabase,
  LucideHouse,
  LucideMenu,
  LucidePanelLeftClose,
  LucidePanelLeftOpen,
  LucideRefreshCw
} from '@lucide/angular';
import { RouterLink, RouterLinkActive, RouterOutlet } from '@angular/router';
import { map } from 'rxjs';
import { toSignal } from '@angular/core/rxjs-interop';

import { DashboardStore } from '../../features/dashboard/data-access/dashboard-store';

@Component({
  selector: 'app-application-shell',
  imports: [
    DatePipe,
    MatButtonModule,
    MatDividerModule,
    MatMenuModule,
    MatSidenavModule,
    MatToolbarModule,
    MatTooltipModule,
    LucideDatabase,
    LucideHouse,
    LucideMenu,
    LucidePanelLeftClose,
    LucidePanelLeftOpen,
    LucideRefreshCw,
    RouterLink,
    RouterLinkActive,
    RouterOutlet
  ],
  templateUrl: './application-shell.html',
  styleUrl: './application-shell.sass'
})
export class ApplicationShell {
  readonly dashboardStore = inject(DashboardStore);
  private readonly breakpointObserver = inject(BreakpointObserver);

  readonly drawerOpen = signal(false);
  readonly manuallyCollapsed = signal(false);
  readonly isHandset = toSignal(
    this.breakpointObserver.observe('(max-width: 959px)').pipe(map(result => result.matches)),
    { initialValue: false }
  );
  readonly isCompact = toSignal(
    this.breakpointObserver.observe('(min-width: 960px) and (max-width: 1199px)').pipe(
      map(result => result.matches)
    ),
    { initialValue: false }
  );
  readonly collapsed = computed(() => !this.isHandset() && (this.isCompact() || this.manuallyCollapsed()));
  readonly sidenavMode = computed(() => this.isHandset() ? 'over' as const : 'side' as const);
  readonly sidenavOpened = computed(() => this.isHandset() ? this.drawerOpen() : true);

  toggleNavigation(): void {
    if (this.isHandset()) {
      this.drawerOpen.update(open => !open);
    } else if (!this.isCompact()) {
      this.manuallyCollapsed.update(collapsed => !collapsed);
    }
  }

  closeHandsetNavigation(): void {
    if (this.isHandset()) {
      this.drawerOpen.set(false);
    }
  }
}