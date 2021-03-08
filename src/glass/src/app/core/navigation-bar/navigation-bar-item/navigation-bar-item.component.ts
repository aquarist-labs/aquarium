import { Component, Input, OnInit } from '@angular/core';
import { Router } from '@angular/router';

export type NavItem = {
  name: string;
  icon: string;
  route?: string;
  children?: NavItem[];
};

@Component({
  selector: 'glass-navigation-bar-item',
  templateUrl: './navigation-bar-item.component.html',
  styleUrls: ['./navigation-bar-item.component.scss']
})
export class NavigationBarItemComponent implements OnInit {
  @Input() item!: NavItem;
  @Input() depth = 0;
  showSub = false;

  constructor(private router: Router) {}

  ngOnInit(): void {}

  itemClicked(item: NavItem) {
    if (!item.children || !item.children.length) {
      this.router.navigate([item.route]);
    } else if (item.children && item.children.length) {
      this.showSub = !this.showSub;
    }
  }
}
