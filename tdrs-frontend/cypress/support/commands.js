/* eslint-disable no-undef */

// ***********************************************
// This example commands.js shows you how to
// create various custom commands and overwrite
// existing commands.
//
// For more comprehensive examples of custom
// commands please read more here:
// https://on.cypress.io/custom-commands
// ***********************************************
//
//
// -- This is a parent command --
// Cypress.Commands.add('login', (email, password) => { ... })
//
//
// -- This is a child command --
// Cypress.Commands.add('drag', { prevSubject: 'element'}, (subject, options) => { ... })
//
//
// -- This is a dual command --
// Cypress.Commands.add('dismiss', { prevSubject: 'optional'}, (subject, options) => { ... })
//
//
// -- This will overwrite an existing command --
// Cypress.Commands.overwrite('visit', (originalFn, url, options) => { ... })

Cypress.Commands.add('login', (username) =>
  cy
    .request({
      method: 'POST',
      url: `${Cypress.env('apiUrl')}/login/cypress`,
      body: {
        username,
        token: Cypress.env('cypressToken'),
      },
    })
    .then((response) => {
      cy.window()
        .its('store')
        .invoke('dispatch', {
          type: 'SET_AUTH',
          payload: {
            user: {
              email: username,
            },
          },
        })
    })
)