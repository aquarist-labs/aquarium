import { HttpClientTestingModule } from '@angular/common/http/testing';
import { NgModule } from '@angular/core';
import { NoopAnimationsModule } from '@angular/platform-browser/animations';
import { RouterTestingModule } from '@angular/router/testing';

@NgModule({
  imports: [HttpClientTestingModule, NoopAnimationsModule, RouterTestingModule],
  exports: [RouterTestingModule]
})
export class TestingModule {}
