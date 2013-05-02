" Vim syntax file
" Language: Pipeline Creation Language
" Maintainer: Ian Johnson
" Latest Revision: 18 March 2013

if version < 600
  syntax clear
elseif exists("b:current_syntax")
  finish
endif

syn keyword pclKeywords as component configuration declare
syn keyword pclKeywords input inputs output outputs
syn keyword pclKeywords merge new split wire with
syn keyword pclStatement component nextgroup=pclIdentifier skipwhite
syn keyword pclImports import

syn match pclComment "#.*$"
syn match pclIdentifier "\h\+"
syn match pclQualifiedIdentifier "\h\+\(\.\h\+\)\+"
syn match pclOperators ":=\|->\|>>>\|\*\*\*\|&&&\|first\|second"

hi def link pclKeywords Statement
hi def link pclStatement Statement
hi def link pclOperators Operator
hi def link pclQualifiedIdentifier Identifier
hi def link pclIdentifier Type
hi def link pclImports Include
hi def link pclComment Comment

let b:current_syntax = "pcl"
" Options for vi: ts=2 sw=2 sts=2 nowrap noexpandtab ft=vimi
