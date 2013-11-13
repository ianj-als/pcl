" Vim syntax file
" Language: Pipeline Creation Language
" Maintainer: Ian Johnson
" Latest Revision: 5 November 2013

if version < 600
  syntax clear
elseif exists("b:current_syntax")
  finish
endif

syn keyword pclKeywords and as bottom component configuration declare do
syn keyword pclKeywords else endif if in input inputs or output outputs
syn keyword pclKeywords let merge new return split then top wire with xor
syn keyword pclStatement component nextgroup=pclIdentifier skipwhite
syn keyword pclImports import

syn match pclComment "#.*$"
syn match pclIdentifier "\h\+"
syn match pclQualifiedIdentifier "\h\+\(\.\h\+\)\+"
syn match pclStateIdentifier "@\h\+"
syn match pclStateQualifiedIdentifier "@\h\+\(\.\h\+\)\+"
syn match pclOperators ":=\|->\|<-\|>>>\|\*\*\*\|&&&\|first\|second"

syn region pclString start=/\v"/ skip=/\v\\./ end=/\v"/

hi def link pclKeywords Statement
hi def link pclStatement Statement
hi def link pclOperators Operator
hi def link pclQualifiedIdentifier Identifier
hi def link pclIdentifier Type
hi def link pclStateQualifiedIdentifier Debug
hi def link pclStateIdentifier Debug
hi def link pclImports Include
hi def link pclComment Comment
hi def link pclString String

let b:current_syntax = "pcl"
" Options for vi: ts=2 sw=2 sts=2 nowrap noexpandtab ft=vimi
