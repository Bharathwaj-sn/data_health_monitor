import { DatePipe } from '@angular/common';
import { Component, inject } from '@angular/core';
import { MatButtonModule } from '@angular/material/button';
import { MatProgressSpinnerModule } from '@angular/material/progress-spinner';
import { LucideCircleAlert, LucideRefreshCw } from '@lucide/angular';

import { UnityCatalogTree } from '../unity-catalog/unity-catalog-tree';
import { DashboardStore } from './data-access/dashboard-store';

@Component({
  selector: 'app-dashboard-page',
  imports: [
    DatePipe,
    MatButtonModule,
    MatProgressSpinnerModule,
    LucideCircleAlert,
    LucideRefreshCw,
    UnityCatalogTree
  ],
  templateUrl: './dashboard-page.html',
  styleUrl: './dashboard-page.sass'
})
export class DashboardPage {
  readonly store = inject(DashboardStore);

  reloadStatus(): void {
    this.store.reloadIdentity();
    this.store.reloadMetadata();
  }
}