declare global {
  namespace Cypress {
    interface Chainable<Subject> {
      clickButton(label: string): Chainable<Subject>;
    }
  }
}

/**
 * Press the first found button with the given text.
 */
Cypress.Commands.add('clickButton', (text: string) => {
  return cy.get(`button:contains("${text}")`).should('be.visible').click();
});
