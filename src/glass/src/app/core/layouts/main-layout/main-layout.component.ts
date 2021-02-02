import { Component, OnInit } from '@angular/core';
import { MatDrawerMode } from '@angular/material/sidenav/drawer';

@Component({
  selector: 'glass-main-layout',
  templateUrl: './main-layout.component.html',
  styleUrls: ['./main-layout.component.scss'],
})
export class MainLayoutComponent implements OnInit {
  public sideNavMode: MatDrawerMode = 'side';
  public sideNavOpened = false;

  constructor() {}

  ngOnInit(): void {}
}
