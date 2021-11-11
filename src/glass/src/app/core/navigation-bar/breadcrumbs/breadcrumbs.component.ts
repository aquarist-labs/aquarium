import { Component, OnDestroy } from '@angular/core';
import { ActivatedRoute, NavigationEnd, Router } from '@angular/router';
import { Subscription } from 'rxjs';
import { distinctUntilChanged, filter } from 'rxjs/operators';

@Component({
  selector: 'glass-breadcrumbs',
  templateUrl: './breadcrumbs.component.html',
  styleUrls: ['./breadcrumbs.component.scss']
})
export class BreadcrumbsComponent implements OnDestroy {
  breadcrumbs: IBreadcrumb[] = [];
  subscription: Subscription;

  constructor(private router: Router, private activatedRoute: ActivatedRoute) {
    this.breadcrumbs = this.buildBreadCrumb(this.activatedRoute.root);
    this.subscription = this.router.events
      .pipe(
        filter((x) => x instanceof NavigationEnd),
        distinctUntilChanged()
      )
      .subscribe(() => {
        this.breadcrumbs = this.buildBreadCrumb(this.activatedRoute.root);
      });
  }

  ngOnDestroy(): void {
    this.subscription.unsubscribe();
  }

  private buildBreadCrumb(
    route: ActivatedRoute,
    url: string = '',
    breadcrumbs: IBreadcrumb[] = []
  ): IBreadcrumb[] {
    let path: string = route.routeConfig?.path || '';
    let label = route.routeConfig?.data?.breadcrumb || '';

    // With parameter
    const lastRoutePart = path.split('/').pop() || '';
    const hasParam = lastRoutePart.startsWith(':') && !!route.snapshot;
    if (hasParam) {
      const param = route.snapshot.params[lastRoutePart.split(':')[1]];
      path = path.replace(lastRoutePart, param);
      label += ' ' + decodeURIComponent(param);
    }

    const nextUrl = path ? `${url}/${path}` : url;
    if (label !== '') {
      breadcrumbs.push({
        label,
        path: nextUrl
      });
    }
    if (route.firstChild) {
      return this.buildBreadCrumb(route.firstChild, nextUrl, breadcrumbs);
    }
    return breadcrumbs;
  }
}

interface IBreadcrumb {
  label: string;
  path: string | null;
}
