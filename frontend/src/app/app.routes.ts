import { Routes } from '@angular/router';

import { ApplicationShell } from './layout/application-shell/application-shell';

export const routes: Routes = [
	{
		path: '',
		component: ApplicationShell,
		children: [
			{
				path: 'dashboard',
				loadComponent: () => import('./features/dashboard/dashboard-page').then(module => module.DashboardPage)
			},
			{
				path: '',
				pathMatch: 'full',
				redirectTo: 'dashboard'
			},
			{
				path: '**',
				redirectTo: 'dashboard'
			}
		]
	}
];
