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
    let label = route.routeConfig?.data?.breadcrumb || '';
    let path: string = route.routeConfig?.data ? (route.routeConfig.path as string) : '';

    // If the route is dynamic route such as ':id', remove it
    const lastRoutePart = path.split('/').pop() || '';
    if (lastRoutePart.startsWith(':') && !!route.snapshot) {
      const paramName = lastRoutePart.split(':')[1];
      path = path.replace(lastRoutePart, route.snapshot.params[paramName]);
      label += ' ' + route.snapshot.params[paramName];
    }

    const nextUrl = path ? `${url}/${path}` : url;
    const breadcrumb: IBreadcrumb = {
      label,
      path: nextUrl
    };
    const newBreadcrumbs = breadcrumb.label ? [...breadcrumbs, breadcrumb] : [...breadcrumbs];
    if (route.firstChild) {
      return this.buildBreadCrumb(route.firstChild, nextUrl, newBreadcrumbs);
    }
    return newBreadcrumbs;
  }
}

interface IBreadcrumb {
  label: string;
  path: string | null;
}
